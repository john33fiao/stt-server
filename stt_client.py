import sys
import time
import threading
import requests
import os
from typing import Optional
from RealtimeSTT import AudioToTextRecorder

# ==========================================
# 설정 (환경 변수 또는 기본값 사용 권장)
# ==========================================
CONFIG = {
    "API_ENDPOINT": os.getenv("STT_API_URL", "http://localhost:5000/api/stt"),
    "SEND_INTERVAL": 5,
    "TIMEOUT": 5,
    "MAX_RETRIES": 1,
    "WHISPER_MODEL": "base",
    "LANGUAGE": "ko"
}

# ==========================================
# 전역 변수 & 락
# ==========================================
text_buffer: str = ""
buffer_lock = threading.Lock()

stats = {
    'total_sends': 0,
    'successful_sends': 0,
    'failed_sends': 0,
    'total_chars': 0
}
stats_lock = threading.Lock()


def send_to_api(text: str) -> bool:
    """API로 텍스트 전송 (동기식)"""
    if not text or not text.strip():
        return False

    payload = {
        'text': text,
        'timestamp': int(time.time())
    }

    retries = 0
    while retries <= CONFIG["MAX_RETRIES"]:
        try:
            response = requests.post(
                CONFIG["API_ENDPOINT"],
                json=payload,
                timeout=CONFIG["TIMEOUT"]
            )

            if response.status_code == 200:
                with stats_lock:
                    stats['successful_sends'] += 1
                    stats['total_chars'] += len(text)
                
                # 로그 가독성을 위해 텍스트 길이에 따라 자르기
                display_text = (text[:30] + '..') if len(text) > 30 else text
                print(f"[✓] 전송 성공 (ID: {response.json().get('message_id')}) - \"{display_text}\"")
                return True

            elif 400 <= response.status_code < 500:
                print(f"[✗] 전송 실패 (클라이언트 에러 {response.status_code}): {response.text}")
                break # 4xx는 재시도 의미 없음

            else:
                print(f"[!] 서버 에러 {response.status_code}, 재시도 중... ({retries + 1}/{CONFIG['MAX_RETRIES'] + 1})")

        except requests.exceptions.RequestException as e:
            print(f"[!] 네트워크 오류: {str(e)}, 재시도 중... ({retries + 1}/{CONFIG['MAX_RETRIES'] + 1})")

        retries += 1
        if retries <= CONFIG["MAX_RETRIES"]:
            time.sleep(1)

    with stats_lock:
        stats['failed_sends'] += 1
    print(f"[✗] 전송 최종 실패")
    return False


def timer_thread_func():
    """주기적으로 버퍼 내용을 전송"""
    print(f"[i] 타이머 스레드 시작 (주기: {CONFIG['SEND_INTERVAL']}초)")
    
    while True:
        time.sleep(CONFIG['SEND_INTERVAL'])
        
        text_to_send = ""
        with buffer_lock:
            if text_buffer.strip():
                text_to_send = text_buffer
                # 전송 시도 전 버퍼 비움 (전송 실패 시 데이터 소실 가능성보다 중복 전송 방지 우선)
                # 안전성을 높이려면 전송 성공 후 비우는 로직으로 변경 필요
                global text_buffer
                text_buffer = ""
        
        if text_to_send:
            send_to_api(text_to_send)


def on_realtime_transcription_update(text: str):
    """실시간 중간 결과 출력"""
    # 이전 출력 잔여물을 지우기 위한 패딩 추가
    padding = " " * 20
    sys.stdout.write(f"\r[실시간] {text}{padding}")
    sys.stdout.flush()


def process_final_text(text: str):
    """확정된 문장 처리"""
    global text_buffer
    
    if not text or not text.strip():
        return

    # 실시간 라인 지우기
    sys.stdout.write(f"\r{' ' * 100}\r")
    sys.stdout.flush()

    print(f"[확정] {text}")

    with buffer_lock:
        if text_buffer:
            text_buffer += " "
        text_buffer += text.strip()


def stats_thread_func():
    """통계 모니터링"""
    while True:
        time.sleep(60)
        with stats_lock:
            total = stats['total_sends']
            success = stats['successful_sends']
            # Division by zero 방지
            rate = (success / total * 100) if total > 0 else 0.0
            
            print(f"\n{'='*40}")
            print(f" [통계] 성공률: {rate:.1f}% ({success}/{total})")
            print(f" [통계] 누적 글자수: {stats['total_chars']}")
            print(f"{'='*40}\n")


def main():
    print("="*60)
    print(f"STT Client Started | Model: {CONFIG['WHISPER_MODEL']} | Lang: {CONFIG['LANGUAGE']}")
    print("="*60)

    recorder: Optional[AudioToTextRecorder] = None

    try:
        recorder = AudioToTextRecorder(
            model=CONFIG["WHISPER_MODEL"],
            language=CONFIG["LANGUAGE"],
            spinner=False,
            on_realtime_transcription_update=on_realtime_transcription_update,
            # post_speech_silence_duration 등 추가 옵션 조절 가능
        )
        print("[✓] Recorder Initialized")

        # 데몬 스레드로 설정 (메인 종료 시 자동 종료)
        threading.Thread(target=timer_thread_func, daemon=True).start()
        threading.Thread(target=stats_thread_func, daemon=True).start()

        print("\n[i] Listening... (Ctrl+C to exit)\n")

        while True:
            # [중요 변경] 콜백 방식이 아닌 반환값 처리 방식으로 변경 (라이브러리 표준)
            full_sentence = recorder.text()
            if full_sentence:
                process_final_text(full_sentence)

    except KeyboardInterrupt:
        print("\n[i] Stopping...")
    except Exception as e:
        print(f"\n[✗] Critical Error: {e}")
    finally:
        if recorder:
            recorder.shutdown()
        
        # 종료 전 남은 버퍼 처리
        with buffer_lock:
            if text_buffer.strip():
                print("[i] Sending remaining buffer...")
                send_to_api(text_buffer)
        print("[i] Byte.")

if __name__ == "__main__":
    main()