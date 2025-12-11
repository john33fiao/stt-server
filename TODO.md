# STT 실시간 자막 시스템 - 구현 체크리스트

## 프로젝트 개요
RealtimeSTT 기반 실시간 음성-텍스트 변환 시스템
- 10초마다 REST API로 텍스트 전송
- 95% 전송 성공률 목표 (5% 유실 허용)
- 테스트용 웹 인터페이스 포함

---

## Phase 1: MVP 구현 (필수)

### [ ] 1. 프로젝트 초기 설정
- [x] 프로젝트 디렉토리 구조 생성
  ```
  stt_system/
  ├── api_server.py
  ├── stt_client.py
  ├── templates/
  │   └── index.html
  ├── logs/
  ├── requirements.txt
  └── README.md
  ```
- [x] `.gitignore` 생성
  - [x] `logs/` 디렉토리
  - [x] `__pycache__/`
  - [x] `*.pyc`
  - [x] `.env`

---

### [ ] 2. requirements.txt 작성
```txt
RealtimeSTT==0.1.18
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
```
- [x] 파일 생성 및 내용 작성
- [ ] 가상환경에서 테스트 설치 확인

---

### [ ] 3. REST API 서버 구현 (api_server.py)

#### [x] 3.1 기본 Flask 앱 구조
- [x] Flask 앱 초기화
- [x] CORS 설정
- [x] 포트 5000 바인딩

#### [x] 3.2 데이터 저장소
- [x] 메모리 기반 메시지 리스트 생성
- [x] 타임스탬프 포함 구조 설계
  ```python
  messages = []  # [{text, timestamp, id}, ...]
  ```

#### [x] 3.3 API 엔드포인트 구현
- [x] `POST /api/stt` - 텍스트 수신
  - [x] 요청 JSON 파싱 (`text`, `timestamp`)
  - [x] 메시지 ID 자동 생성
  - [x] 메모리에 저장
  - [x] HTTP 200 응답 반환
  - [x] 에러 처리 (400, 500)

- [x] `GET /api/messages` - 저장된 메시지 조회
  - [x] 전체 메시지 리스트 반환 (JSON)
  - [x] 최근 순서로 정렬 옵션
  - [ ] 페이지네이션 (선택사항)

- [x] `GET /` - 웹페이지 서빙
  - [x] templates/index.html 렌더링

#### [x] 3.4 로깅
- [x] 콘솔 로그 설정
- [x] 수신한 텍스트 로깅
- [x] 에러 로깅

#### [ ] 3.5 테스트
- [ ] curl로 POST 테스트
  ```bash
  curl -X POST http://localhost:5000/api/stt \
    -H "Content-Type: application/json" \
    -d '{"text":"테스트", "timestamp":1702300000}'
  ```
- [ ] GET 엔드포인트 테스트
- [ ] 에러 케이스 테스트

---

### [ ] 4. 웹 인터페이스 구현 (templates/index.html)

#### [x] 4.1 HTML 구조
- [x] 기본 HTML5 템플릿
- [x] 타이틀: "STT 실시간 자막"
- [x] 메시지 표시 영역 (`<div id="messages">`)
- [x] 상태 표시 영역 (연결 상태, 통계)

#### [x] 4.2 CSS 스타일링
- [x] 메시지 컨테이너 스타일
  - [x] 스크롤 가능
  - [x] 자동 하단 스크롤
  - [x] 가독성 좋은 폰트
- [x] 타임스탬프 스타일 (회색, 작은 글씨)
- [x] 상태 표시 스타일 (성공: 녹색, 오류: 빨간색)

#### [x] 4.3 JavaScript 구현
- [x] Polling 방식으로 메시지 가져오기
  - [x] 1초마다 `GET /api/messages` 호출
  - [x] 새 메시지만 추가 (중복 방지)
- [x] 메시지 DOM 추가 로직
  - [x] 타임스탬프 포맷팅
  - [x] append 방식으로 하단에 추가
  - [x] 자동 스크롤
- [x] 에러 처리
  - [x] API 연결 실패 시 상태 표시
  - [x] 재연결 시도

#### [x] 4.4 통계 표시 (선택사항)
- [x] 총 수신 메시지 수
- [x] 마지막 업데이트 시간

---

### [ ] 5. STT 클라이언트 구현 (stt_client.py)

#### [x] 5.1 RealtimeSTT 초기화
- [x] `AudioToTextRecorder` 생성
- [x] 모델: `base`
- [x] 언어: `ko`
- [x] 실시간 변환 활성화
- [x] 콜백 함수 등록

#### [x] 5.2 텍스트 버퍼 관리
- [x] 전역 버퍼 변수 생성
- [x] Lock 객체 생성 (스레드 안전)
- [x] 버퍼 추가 함수
  - [x] Lock 획득/해제
  - [x] 문장 구분 (공백 또는 개행)

#### [x] 5.3 콜백 함수
- [x] 중간 결과 콜백
  - [x] 콘솔에 실시간 표시 (한 줄 갱신)
- [x] 최종 결과 콜백
  - [x] 버퍼에 추가
  - [x] 확정 문장 로깅

#### [x] 5.4 타이머 스레드
- [x] 10초마다 실행
- [x] 버퍼 확인 로직
  - [x] 버퍼 비어있으면 Skip
  - [x] 있으면 전송 함수 호출

#### [x] 5.5 전송 함수
- [x] Lock으로 버퍼 복사 및 비우기
- [x] HTTP POST 요청
  - [x] API 엔드포인트: `http://localhost:5000/api/stt`
  - [x] 타임아웃: 5초
  - [x] JSON 페이로드: `{text, timestamp}`
- [x] 재시도 로직 (1회)
  - [x] 네트워크 에러 시 재시도
  - [x] HTTP 5xx 시 재시도
  - [x] HTTP 4xx 시 재시도 안 함
- [x] 로깅
  - [x] 성공: 전송 문자 수
  - [x] 실패: 에러 메시지

#### [x] 5.6 에러 처리
- [x] 마이크 초기화 실패 처리
- [x] Whisper 모델 로딩 실패 처리
- [x] 예외 발생 시 프로그램 중단 방지

#### [x] 5.7 메인 루프
- [x] 레코더 시작
- [x] 타이머 스레드 시작
- [x] KeyboardInterrupt 처리
- [x] 종료 시 정리 (레코더 shutdown)

#### [x] 5.8 통계 출력 (선택사항)
- [x] 1분마다 통계 출력
  - [x] 총 전송 횟수
  - [x] 성공/실패 횟수
  - [x] 총 문자 수

---

### [ ] 6. README.md 작성

#### [x] 6.1 프로젝트 소개
- [x] 시스템 개요
- [x] 주요 기능
- [x] 아키텍처 다이어그램 (선택)

#### [x] 6.2 설치 가이드
- [x] Python 버전 요구사항 (3.10 이상)
- [x] 가상환경 생성 방법
- [x] 의존성 설치
  ```bash
  pip install -r requirements.txt
  ```
- [x] 시스템 의존성 (PortAudio, ffmpeg)
  - [x] macOS 설치 방법
  - [x] Ubuntu 설치 방법
  - [x] Windows 설치 방법 (선택)

#### [x] 6.3 실행 가이드
- [x] API 서버 실행
  ```bash
  python api_server.py
  ```
- [x] 브라우저에서 확인
  ```
  http://localhost:5000
  ```
- [x] STT 클라이언트 실행
  ```bash
  python stt_client.py
  ```
- [x] 종료 방법 (Ctrl+C)

#### [x] 6.4 설정
- [x] API 엔드포인트 변경 방법
- [x] 전송 주기 변경 방법
- [x] Whisper 모델 변경 방법

#### [x] 6.5 트러블슈팅
- [x] 마이크 권한 문제
- [x] 포트 충돌 문제
- [x] 모델 다운로드 실패
- [x] 메모리 부족

#### [x] 6.6 제한사항
- [x] 5% 유실 허용 설계
- [x] 메모리 저장 (재시작 시 초기화)
- [x] 단일 마이크만 지원

---

## Phase 2: 개선 사항 (선택)

### [ ] 7. 설정 파일 (config.yaml)
- [ ] YAML 파일 생성
- [ ] STT 설정 (model, language, interval)
- [ ] API 설정 (endpoint, timeout, retry)
- [ ] 로깅 설정 (level, file)
- [ ] 코드에서 설정 로딩 로직 추가

---

### [ ] 8. 실행 스크립트 (start.sh)
- [ ] API 서버 백그라운드 실행
- [ ] 브라우저 자동 열기
- [ ] STT 클라이언트 실행
- [ ] Ctrl+C 시 모든 프로세스 종료
- [ ] 실행 권한 부여 (`chmod +x start.sh`)

---

### [ ] 9. 로깅 개선
- [ ] 파일 로깅 추가
  - [ ] 날짜별 로그 파일
  - [ ] 로그 로테이션 (7일치)
- [ ] 로그 레벨 설정 (DEBUG, INFO, ERROR)
- [ ] 구조화된 로그 포맷

---

### [ ] 10. WebSocket 전환 (선택)
- [ ] Flask-SocketIO 추가
- [ ] API 서버에 WebSocket 엔드포인트
- [ ] 웹페이지에서 WebSocket 연결
- [ ] 실시간 푸시 방식으로 변경

---

## Phase 3: 고도화 (나중에)

### [ ] 11. 테스트 코드
- [ ] API 서버 단위 테스트
- [ ] STT 클라이언트 테스트
- [ ] 통합 테스트
- [ ] 테스트 오디오 파일 준비

---

### [ ] 12. Docker 컨테이너화
- [ ] Dockerfile 작성
- [ ] docker-compose.yml 작성
- [ ] 오디오 디바이스 매핑 설정
- [ ] 빌드 및 실행 테스트

---

### [ ] 13. 모니터링 대시보드
- [ ] 통계 차트 (Chart.js)
- [ ] 실시간 성공률 표시
- [ ] 시간대별 전송량 그래프

---

## 체크리스트 진행 방법

1. **순차 진행**: Phase 1을 완료한 후 Phase 2로
2. **테스트 우선**: 각 컴포넌트 구현 후 즉시 테스트
3. **점진적 개선**: 동작하는 최소 버전을 먼저 만들고 개선
4. **문서화**: 변경사항 발생 시 README 업데이트

---

## 예상 소요 시간

- **Phase 1 (MVP)**: 2시간
- **Phase 2 (개선)**: 1시간
- **Phase 3 (고도화)**: 3시간 이상

**권장**: Phase 1 완료 후 실제 사용해보고 Phase 2 진행 여부 결정

---

## 완료 기준

### Phase 1 완료 체크
- [ ] API 서버가 정상 실행됨
- [ ] 웹페이지에서 메시지가 실시간으로 표시됨
- [ ] STT 클라이언트가 음성을 인식하고 10초마다 전송함
- [ ] curl로 API 테스트 성공
- [ ] README 가이드대로 다른 사람이 실행 가능

### 전체 완료 체크
- [ ] 모든 Phase 1~3 항목 체크
- [ ] 버그 없이 1시간 이상 안정적 실행
- [ ] 문서화 완료