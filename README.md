# STT 실시간 자막 시스템

RealtimeSTT 기반 실시간 음성-텍스트 변환 시스템

## 주요 기능

- 실시간 음성 인식 및 텍스트 변환
- 10초마다 자동으로 REST API로 텍스트 전송
- 95% 전송 성공률 목표 (5% 유실 허용)
- 실시간 자막 표시 웹 인터페이스
- 자동 재시도 및 에러 처리

## 시스템 구조

```
STT Client (마이크) → API Server → Web Interface (브라우저)
```

## 설치 가이드

### 요구사항

- Python 3.10 이상
- 마이크 (음성 입력)
- ffmpeg 및 PortAudio

### 시스템 의존성 설치

#### Windows
```bash
# ffmpeg 설치 (Chocolatey 사용)
choco install ffmpeg

# 또는 https://ffmpeg.org/download.html 에서 수동 설치
```

#### macOS
```bash
brew install portaudio ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev ffmpeg
```

### Python 의존성 설치

1. **가상환경 생성 (권장)**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

## 실행 가이드

### 1. API 서버 실행

```bash
python api_server.py
```

서버가 `http://localhost:5000` 에서 실행됩니다.

### 2. 웹 인터페이스 확인

브라우저에서 다음 주소로 접속:
```
http://localhost:5000
```

### 3. STT 클라이언트 실행

새 터미널을 열고:

```bash
python stt_client.py
```

마이크에 대고 말하면 자막이 웹 인터페이스에 실시간으로 표시됩니다.

### 4. 종료

각 프로그램에서 `Ctrl+C` 를 눌러 종료합니다.

## 설정

### API 엔드포인트 변경

`stt_client.py` 파일에서 다음 변수를 수정:

```python
API_ENDPOINT = "http://localhost:5000/api/stt"
```

### 전송 주기 변경

```python
SEND_INTERVAL = 10  # 초 단위
```

### Whisper 모델 변경

```python
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
```

모델 크기가 클수록 정확도는 높지만 리소스 사용량도 증가합니다.

### 언어 변경

```python
LANGUAGE = "ko"  # en, ja, zh 등
```

## API 엔드포인트

### POST /api/stt
STT 텍스트를 수신합니다.

**요청 예시:**
```bash
curl -X POST http://localhost:5000/api/stt \
  -H "Content-Type: application/json" \
  -d '{"text":"안녕하세요", "timestamp":1702300000}'
```

**응답:**
```json
{
  "status": "success",
  "message_id": 1
}
```

### GET /api/messages
저장된 모든 메시지를 조회합니다.

**요청 예시:**
```bash
curl http://localhost:5000/api/messages
```

**응답:**
```json
{
  "status": "success",
  "count": 10,
  "messages": [
    {
      "id": 1,
      "text": "안녕하세요",
      "timestamp": 1702300000
    }
  ]
}
```

## 트러블슈팅

### 마이크 권한 문제

**Windows**: 설정 → 개인정보 → 마이크 → 앱이 마이크에 액세스하도록 허용

**macOS**: 시스템 환경설정 → 보안 및 개인정보 보호 → 마이크 → Python 허용

**Linux**: PulseAudio/ALSA 설정 확인

### 포트 충돌 문제

5000 포트가 이미 사용 중인 경우:

`api_server.py` 파일 마지막 줄 수정:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

그리고 `stt_client.py`의 API_ENDPOINT도 변경:
```python
API_ENDPOINT = "http://localhost:5001/api/stt"
```

### Whisper 모델 다운로드 실패

인터넷 연결을 확인하고 재시도하세요. 최초 실행 시 모델 다운로드에 시간이 걸립니다.

### 메모리 부족

더 작은 Whisper 모델 사용:
```python
WHISPER_MODEL = "tiny"  # 가장 작은 모델
```

### "No module named 'RealtimeSTT'"

의존성을 다시 설치:
```bash
pip install --upgrade RealtimeSTT
```

### 음성 인식이 안 됨

1. 마이크가 올바르게 연결되어 있는지 확인
2. 시스템 기본 마이크 설정 확인
3. 마이크 볼륨 확인

## 제한사항

- **5% 유실 허용**: 네트워크 장애 시 일부 메시지가 유실될 수 있습니다
- **메모리 저장**: 서버 재시작 시 모든 메시지가 초기화됩니다
- **단일 마이크**: 동시에 하나의 마이크만 지원합니다
- **단일 클라이언트**: 한 번에 하나의 STT 클라이언트만 실행하세요

## 디렉토리 구조

```
STT_Server/
├── api_server.py          # REST API 서버
├── stt_client.py          # STT 클라이언트
├── templates/
│   └── index.html         # 웹 인터페이스
├── logs/                  # 로그 파일 (자동 생성)
├── requirements.txt       # Python 의존성
├── .gitignore
└── README.md
```

## 통계 및 모니터링

STT 클라이언트는 1분마다 다음 통계를 출력합니다:
- 총 전송 횟수
- 성공/실패 횟수
- 성공률 (%)
- 총 전송 문자 수

웹 인터페이스에서도 실시간으로 확인 가능:
- 총 메시지 수
- 마지막 업데이트 시간
- 연결 상태

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다.
