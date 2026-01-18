# 웹 기반 얼굴 표정 & 졸음 감지 시스템

브라우저에서 실행되는 실시간 얼굴 표정 및 졸음 감지 시스템입니다.

## 기능

- **눈 감김 감지 (EAR)**: Eye Aspect Ratio 기반 졸음 감지
- **하품 감지 (MAR)**: Mouth Aspect Ratio 기반 하품 감지
- **감정 인식**: MediaPipe Face Landmarker blendshape 기반 요약 (neutral, happy, frown, surprise)
- **실시간 알림**: 브라우저 알림 및 경고음
- **이벤트 로깅**: WebSocket을 통한 서버 이벤트 전송
- **GPU 가속**: MediaPipe WebAssembly + SIMD (브라우저 최적화)

## 기술 스택

### Frontend
- React 18 + TypeScript
- MediaPipe Tasks (Face Landmarker + blendshape)
- Tailwind CSS
- Vite

### Backend
- FastAPI
- PostgreSQL + TimescaleDB
- Redis
- WebSocket

## 시작하기

### 사전 요구사항

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose (선택)

### 개발 환경 설정

1. **face-api.js 모델 다운로드**
   > MediaPipe로 교체되었습니다. 기존 face-api.js 모델은 더 이상 필요하지 않습니다.

> 기본적으로 CDN에서 모델을 불러옵니다. 로컬에 두고 싶다면 아래 명령을 실행하세요.
>
> ```bash
> mkdir -p frontend/public/models
> curl -L -o frontend/public/models/face_landmarker.task \
>   https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
> ```

2. **프론트엔드 실행**

```bash
cd frontend
npm install
npm run dev
```

3. **백엔드 실행 (선택)**

```bash
# Docker로 DB 서비스 실행
cd infrastructure
docker compose -f docker-compose.dev.yml up -d

# 백엔드 실행
cd ../backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Docker로 전체 실행

```bash
cd infrastructure
docker compose up --build
```

## 프로젝트 구조

```
facial-detection-web/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/      # UI 컴포넌트
│   │   ├── hooks/           # React 훅
│   │   ├── lib/             # 유틸리티 및 감지 로직
│   │   └── types/           # TypeScript 타입
│   └── public/models/       # MediaPipe 모델 (.task)
├── backend/                  # FastAPI 백엔드
│   └── app/
│       ├── api/             # API 엔드포인트
│       ├── core/            # 설정 및 보안
│       ├── models/          # DB 모델
│       └── services/        # 비즈니스 로직
└── infrastructure/           # Docker 설정
```

## 설정 값

| 항목 | 기본값 | 설명 |
|------|--------|------|
| EAR 임계값 | 0.22 | 눈 감김 판단 기준 |
| MAR 임계값 | 0.6 | 하품 판단 기준 |
| 졸음 감지 시간 | 2.0초 | 눈 감김 지속 시간 |
| 하품 감지 시간 | 1.0초 | 입 벌림 지속 시간 |
| 알림 간격 | 3.0초 | 알림 쿨다운 |
| 카메라 해상도 | 320x240 | 성능 최적화를 위한 저해상도 |

## 성능 최적화

- **MediaPipe Tasks**: WebAssembly + SIMD 최적화
- **저해상도 카메라**: 320x240 해상도로 처리량 최소화
- **브라우저 캐싱**: 모델(.task) 파일을 CDN 대신 로컬 `/public/models`에서 로드

## API 엔드포인트

### REST API

- `GET /health` - 헬스 체크
- `GET /api/events/session/{user_id}/{session_id}` - 세션 통계
- `GET /api/events/user/{user_id}` - 사용자 통계
- `GET /api/events/recent/{user_id}` - 최근 이벤트

### WebSocket

- `ws://localhost:8000/ws/events/{user_id}` - 실시간 이벤트 스트리밍

## 라이선스

MIT License
