import sys
import time
import threading
import requests
from RealtimeSTT import AudioToTextRecorder

# 설정
API_ENDPOINT = "http://localhost:5000/api/stt"
SEND_INTERVAL = 5  # 5초마다 전송
TIMEOUT = 5  # 5초 타임아웃
MAX_RETRIES = 1  # 1회 재시도
WHISPER_MODEL = "turbo"  # tiny, base, small, medium, large, turbo 중 선택 (turbo 추천: 빠르고 정확)
LANGUAGE = "ko"

# 전역 변수
text_buffer = ""
realtime_buffer = ""  # 실시간 중간 결과 저장
buffer_lock = threading.Lock()

# 통계
stats = {
    'total_sends': 0,
    'successful_sends': 0,
    'failed_sends': 0,
    'total_chars': 0
}
stats_lock = threading.Lock()


def send_to_api(text):
    """API로 텍스트 전송"""
    if not text or text.strip() == "":
        return False

    payload = {
        'text': text,
        'timestamp': int(time.time())
    }

    retries = 0
    while retries <= MAX_RETRIES:
        try:
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                # 전송 성공
                with stats_lock:
                    stats['successful_sends'] += 1
                    stats['total_chars'] += len(text)

                print(f"[✓] 전송 성공 (길이: {len(text)}자, ID: {response.json().get('message_id')})")
                return True

            elif 400 <= response.status_code < 500:
                # 4xx 에러는 재시도하지 않음
                print(f"[✗] 전송 실패 (클라이언트 에러 {response.status_code}): {response.text}")
                with stats_lock:
                    stats['failed_sends'] += 1
                return False

            else:
                # 5xx 에러는 재시도
                print(f"[!] 서버 에러 {response.status_code}, 재시도 중... ({retries + 1}/{MAX_RETRIES + 1})")
                retries += 1
                if retries <= MAX_RETRIES:
                    time.sleep(1)

        except requests.exceptions.Timeout:
            print(f"[!] 타임아웃 발생, 재시도 중... ({retries + 1}/{MAX_RETRIES + 1})")
            retries += 1
            if retries <= MAX_RETRIES:
                time.sleep(1)

        except requests.exceptions.ConnectionError:
            print(f"[!] 연결 실패, 재시도 중... ({retries + 1}/{MAX_RETRIES + 1})")
            retries += 1
            if retries <= MAX_RETRIES:
                time.sleep(1)

        except Exception as e:
            print(f"[✗] 전송 중 예외 발생: {str(e)}")
            with stats_lock:
                stats['failed_sends'] += 1
            return False

    # 모든 재시도 실패
    with stats_lock:
        stats['failed_sends'] += 1
    print(f"[✗] 전송 실패 (모든 재시도 실패)")
    return False


def timer_thread():
    """5초마다 버퍼 내용을 전송하는 스레드"""
    global text_buffer, realtime_buffer
    print(f"[i] 타이머 스레드 시작 (전송 주기: {SEND_INTERVAL}초)")

    while True:
        time.sleep(SEND_INTERVAL)

        with buffer_lock:
            # 실시간 버퍼와 확정 버퍼 합치기
            combined_text = ""
            if text_buffer.strip():
                combined_text = text_buffer.strip()
            if realtime_buffer.strip():
                if combined_text:
                    combined_text += " " + realtime_buffer.strip()
                else:
                    combined_text = realtime_buffer.strip()
            
            if combined_text:
                text_to_send = combined_text
                # 버퍼 비우기 (전송 성공 여부와 관계없이)
                text_buffer = ""
                realtime_buffer = ""

                with stats_lock:
                    stats['total_sends'] += 1

                print(f"\n[→] 전송 시작: \"{text_to_send[:50]}...\"")
                send_to_api(text_to_send)
            else:
                print("[i] 전송할 텍스트 없음, 대기 중...")


def on_realtime_transcription_update(text):
    """중간 결과 콜백 (실시간 표시 + 버퍼 적재)"""
    global realtime_buffer
    
    if not text or text.strip() == "":
        return
    
    # 실시간 버퍼에 최신 결과 저장 (덮어쓰기)
    with buffer_lock:
        realtime_buffer = text.strip()
    
    # 한 줄 갱신
    sys.stdout.write(f"\r[실시간] {text}          ")
    sys.stdout.flush()


def process_final_text(text):
    """최종 결과 처리 (버퍼에 추가)"""
    global text_buffer

    if not text or text.strip() == "":
        return

    with buffer_lock:
        # 문장 구분 (공백으로)
        if text_buffer:
            text_buffer += " "
        text_buffer += text.strip()

    # 새로운 줄에 확정 문장 출력
    print(f"\n[확정] {text}")


def stats_thread():
    """1분마다 통계 출력"""
    while True:
        time.sleep(60)

        with stats_lock:
            total = stats['total_sends']
            success = stats['successful_sends']
            failed = stats['failed_sends']
            chars = stats['total_chars']

            success_rate = (success / total * 100) if total > 0 else 0

            print(f"\n{'='*60}")
            print(f"[통계] 전송: {total}회 | 성공: {success}회 | 실패: {failed}회")
            print(f"[통계] 성공률: {success_rate:.1f}% | 총 문자: {chars}자")
            print(f"{'='*60}\n")


def main():
    """메인 함수"""
    print("="*60)
    print("STT 실시간 자막 클라이언트")
    print("="*60)
    print(f"API 엔드포인트: {API_ENDPOINT}")
    print(f"전송 주기: {SEND_INTERVAL}초")
    print(f"Whisper 모델: {WHISPER_MODEL}")
    print(f"언어: {LANGUAGE}")
    print("="*60)

    try:
        # RealtimeSTT 레코더 초기화
        print("\n[i] RealtimeSTT 초기화 중...")
        print("[i] Whisper 모델 다운로드 중... (최초 실행 시 시간이 걸릴 수 있습니다)")

        recorder = AudioToTextRecorder(
            model=WHISPER_MODEL,
            language=LANGUAGE,
            spinner=False,
            silero_sensitivity=0.6,              # 음성 감지 민감도 높임
            post_speech_silence_duration=0.3,    # 음성 종료 판단 시간 단축
            min_length_of_recording=0.5,         # 최소 녹음 길이 단축
            min_gap_between_recordings=0.1,      # 녹음 간 최소 간격 단축
            enable_realtime_transcription=True,  # 실시간 변환 활성화
            on_realtime_transcription_update=on_realtime_transcription_update,
        )

        print("[✓] RealtimeSTT 초기화 완료!")

        # 마이크 입력 시작
        recorder.start()
        print("[i] 마이크 스트림 시작!")

        # 타이머 스레드 시작
        timer = threading.Thread(target=timer_thread, daemon=True)
        timer.start()

        # 통계 스레드 시작
        stats_t = threading.Thread(target=stats_thread, daemon=True)
        stats_t.start()

        print("\n[i] 음성 인식 시작... (Ctrl+C로 종료)")
        print("[i] 마이크에 대고 말씀하세요.\n")

        # 메인 루프 - 실시간 콜백이 버퍼에 적재, 타이머가 전송 담당
        # recorder.text()는 백그라운드에서 확정 문장 처리용으로 유지
        while True:
            try:
                final_text = recorder.text()
                if final_text:
                    process_final_text(final_text)
            except Exception as e:
                # 실시간 전송이 메인이므로 에러 발생해도 계속 진행
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n[i] 종료 신호 수신...")

    except Exception as e:
        print(f"\n[✗] 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 정리
        print("[i] 레코더 종료 중...")
        try:
            recorder.shutdown()
        except:
            pass

        # 남은 버퍼 전송
        with buffer_lock:
            if text_buffer.strip():
                print(f"[i] 남은 텍스트 전송 중...")
                send_to_api(text_buffer)

        # 최종 통계 출력
        with stats_lock:
            print("\n" + "="*60)
            print("최종 통계")
            print("="*60)
            print(f"총 전송: {stats['total_sends']}회")
            print(f"성공: {stats['successful_sends']}회")
            print(f"실패: {stats['failed_sends']}회")
            print(f"총 문자: {stats['total_chars']}자")
            print("="*60)

        print("\n[i] 프로그램 종료")


if __name__ == "__main__":
    main()
