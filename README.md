# Facial Expression & Drowsiness Detection

실시간 얼굴 표정 인식 및 졸림/하품 감지 프로그램입니다.

## 주요 기능

- **표정 인식**: FER 라이브러리를 사용하여 7가지 표정 감지 (angry, disgust, fear, happy, sad, surprise, neutral)
- **졸림 감지**: EAR (Eye Aspect Ratio) 알고리즘으로 눈 감김 상태 측정
- **하품 감지**: MAR (Mouth Aspect Ratio) 알고리즘으로 하품 감지
- **실시간 경고**: 졸림/하품 감지 시 시각적 경고 및 macOS 시스템 경고음 재생

## 기술 스택

| 라이브러리 | 용도 |
|-----------|------|
| OpenCV | 카메라 입력 및 화면 출력 |
| FER | 딥러닝 기반 표정 인식 (MTCNN) |
| dlib | 얼굴 랜드마크 68점 추출 |
| scipy | 유클리드 거리 계산 |

## 알고리즘

### EAR (Eye Aspect Ratio)
눈의 세로/가로 비율로 눈 감김 정도를 측정합니다.
- 임계값: 0.22 미만일 때 눈 감김으로 판단
- 2초 이상 지속 시 졸림 경고

### MAR (Mouth Aspect Ratio)
입의 세로/가로 비율로 하품을 감지합니다.
- 임계값: 0.6 초과일 때 입 벌림으로 판단
- 1초 이상 지속 시 하품 경고

## 설치

### 1. 의존성 설치
```bash
pip install opencv-python numpy fer dlib scipy
```

### 2. dlib 랜드마크 모델 다운로드
```bash
curl -L -o shape_predictor_68_face_landmarks.dat.bz2 http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

## 사용법

### 기본 실행 (내장 카메라)
```bash
python main.py
```

### 특정 카메라 사용
```bash
python main.py -c 1  # 카메라 인덱스 1 사용 (예: iPhone 연속성 카메라)
```

### 사용 가능한 카메라 목록 확인
```bash
python main.py -l
```

## 화면 구성

| 항목 | 설명 |
|-----|------|
| EAR | 현재 눈 종횡비 (낮을수록 눈 감김) |
| MAR | 현재 입 종횡비 (높을수록 입 벌림) |
| Eyes closed | 눈 감은 시간 / 졸림 판단 시간 |
| DROWSY! | 졸림 감지 경고 (빨간색) |
| YAWNING! | 하품 감지 경고 (주황색) |
| Emotion | 현재 감지된 표정 및 신뢰도 |

## 설정값

| 변수 | 기본값 | 설명 |
|-----|-------|------|
| `EAR_THRESHOLD` | 0.22 | 눈 감김 판단 임계값 |
| `MAR_THRESHOLD` | 0.6 | 하품 판단 임계값 |
| `DROWSY_TIME` | 2.0초 | 졸림 판단까지 필요한 시간 |
| `YAWN_TIME` | 1.0초 | 하품 판단까지 필요한 시간 |
| `ALERT_COOLDOWN` | 3.0초 | 경고음 재생 간격 |

## 요구사항

- macOS (경고음 재생에 `afplay` 사용)
- Python 3.x
- 웹캠 또는 연속성 카메라

## 종료

`Ctrl + C` 또는 창 닫기
