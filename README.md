# Facial Expression & Drowsiness Detection

실시간 얼굴 표정 인식 및 졸림/하품 감지 프로그램입니다.

## 주요 기능

- **표정 인식**: MediaPipe Face Landmarker의 blendshape를 활용해 happy/frown/surprise/neutral 요약 및 상위 블렌드셰이프 표시
- **졸림 감지**: EAR (Eye Aspect Ratio) + MediaPipe `eyeBlink*` 블렌드셰이프 조합으로 눈 감김 상태 측정
- **하품 감지**: MAR (Mouth Aspect Ratio) + MediaPipe `jawOpen` 블렌드셰이프 조합으로 하품 감지
- **실시간 경고**: 졸림/하품 감지 시 시각적 경고 및 macOS 시스템 경고음 재생
- **외부 연동**: Named Pipe를 통해 외부 프로그램에 이벤트 전송
- **로그 기록**: 모든 감지 이벤트를 타임스탬프와 함께 파일에 기록

## 기술 스택

| 라이브러리 | 용도 |
|-----------|------|
| OpenCV | 카메라 입력 및 화면 출력 |
| MediaPipe | Face Landmarker로 얼굴/블렌드셰이프 추출 |
| numpy | 계산 및 랜드마크 좌표 처리 |

## 알고리즘

### EAR (Eye Aspect Ratio)
MediaPipe 얼굴 랜드마크로 눈의 세로/가로 비율을 계산합니다.
- 임계값: 0.22 미만일 때 눈 감김으로 판단
- 2초 이상 지속 시 졸림 경고

### MAR (Mouth Aspect Ratio)
MediaPipe 얼굴 랜드마크로 입의 세로/가로 비율을 계산합니다.
- 임계값: 0.6 초과일 때 입 벌림으로 판단
- 1초 이상 지속 시 하품 경고

### MediaPipe Blendshape 신호
- `eyeBlinkLeft/Right` ≥ 0.45: 눈 감김 신호로 활용
- `jawOpen` ≥ 0.35: 입 벌림/하품 신호로 활용
- 표정 요약: `mouthSmile*`, `mouthFrown*`, `browDown*`, `eyeWide*`, `jawOpen` 조합으로 happy/frown/surprise/neutral 산출

## 설치

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. MediaPipe Face Landmarker 모델 다운로드
```bash
mkdir -p models
curl -L -o models/face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
```

## 사용법

```bash
python main.py
```

## 화면 구성

| 항목 | 설명 |
|-----|------|
| EAR | 현재 눈 종횡비 (낮을수록 눈 감김) |
| MAR | 현재 입 종횡비 (높을수록 입 벌림) |
| Blink | MediaPipe `eyeBlink` 블렌드셰이프 스코어 |
| JawOpen | MediaPipe `jawOpen` 블렌드셰이프 스코어 |
| Eyes closed | 눈 감은 시간 / 졸림 판단 시간 |
| DROWSY! | 졸림 감지 경고 (빨간색) |
| YAWNING! | 하품 감지 경고 (주황색) |
| Emotion | 현재 감지된 표정 및 신뢰도 |
| Top blendshapes | 상위 블렌드셰이프 이름/스코어 |

## 설정값

| 변수 | 기본값 | 설명 |
|-----|-------|------|
| `EAR_THRESHOLD` | 0.22 | 눈 감김 판단 임계값 (MediaPipe 랜드마크) |
| `MAR_THRESHOLD` | 0.6 | 하품 판단 임계값 (MediaPipe 랜드마크) |
| `BLINK_SCORE_THRESHOLD` | 0.45 | MediaPipe `eyeBlink*` 블렌드셰이프 임계값 |
| `JAW_OPEN_SCORE_THRESHOLD` | 0.35 | MediaPipe `jawOpen` 블렌드셰이프 임계값 |
| `DROWSY_TIME` | 2.0초 | 졸림 판단까지 필요한 시간 |
| `YAWN_TIME` | 1.0초 | 하품 판단까지 필요한 시간 |
| `ALERT_COOLDOWN` | 3.0초 | 경고음 재생 간격 |

## 요구사항

- macOS (경고음 재생에 `afplay` 사용)
- Python 3.x
- MacBook 내장 카메라

## 외부 프로그램 연동

졸림/하품 감지 시 Named Pipe를 통해 이벤트를 전송합니다. 외부 프로그램에서 실시간으로 상태를 수신할 수 있습니다.

> **Note**: main.py 실행 후 언제든지 리스너를 연결할 수 있습니다. 리스너가 연결되면 자동으로 감지하여 이벤트 전송을 시작합니다.

### 이벤트 종류

| 이벤트 | 설명 |
|-------|------|
| `DROWSY` | 졸림 감지됨 (눈 2초 이상 감음) |
| `YAWN` | 하품 감지됨 (입 1초 이상 벌림) |

### 사용 예시

```bash
# 터미널 1: 얼굴 인식 프로그램 실행
python main.py

# 터미널 2: 이벤트 리스너 실행
python event_listener.py
```

### 예제 프로그램

`examples/` 폴더에 다양한 활용 예제가 있습니다.

| 예제 | 설명 |
|-----|------|
| `drowsy_alert_example.py` | 시스템 사운드 + 알림 센터 + 로그 파일 |
| `drowsy_webhook_example.py` | Slack/Discord/커스텀 서버로 HTTP 전송 |
| `drowsy_automation_example.py` | 화면 밝기, 음악 제어, TTS 음성 경고 |
| `drowsy_statistics_example.py` | 통계 수집 및 피로도 분석 리포트 |

```bash
# 예제 실행
python examples/drowsy_alert_example.py
```

### 직접 구현 시 (Python)

```python
PIPE_PATH = "/tmp/face_status_pipe"

with open(PIPE_PATH, 'r') as pipe:
    while True:
        event = pipe.readline().strip()
        if event == "DROWSY":
            # 졸림 감지 시 처리
            pass
        elif event == "YAWN":
            # 하품 감지 시 처리
            pass
```

### 다른 언어로 구현

#### Shell Script

```bash
#!/bin/bash
while read event; do
    case "$event" in
        DROWSY) echo "졸림 감지!" ;;
        YAWN) echo "하품 감지!" ;;
    esac
done < /tmp/face_status_pipe
```

#### Node.js

```javascript
const fs = require('fs');
const pipe = fs.createReadStream('/tmp/face_status_pipe', { encoding: 'utf8' });

pipe.on('data', (data) => {
    data.trim().split('\n').forEach(event => {
        if (event === 'DROWSY') console.log('졸림 감지!');
        else if (event === 'YAWN') console.log('하품 감지!');
    });
});
```

#### Go

```go
package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    pipe, _ := os.Open("/tmp/face_status_pipe")
    defer pipe.Close()

    scanner := bufio.NewScanner(pipe)
    for scanner.Scan() {
        switch scanner.Text() {
        case "DROWSY":
            fmt.Println("졸림 감지!")
        case "YAWN":
            fmt.Println("하품 감지!")
        }
    }
}
```

## 로그 파일

프로그램 실행 시 자동으로 로그 파일이 생성됩니다.

### 로그 파일 위치
```
detection_YYYYMMDD_HHMMSS.log
```
예: `detection_20260118_060601.log`

### 로그 레벨

| 레벨 | 내용 |
|-----|------|
| DEBUG | EAR/MAR 값 (10프레임마다), 카메라 정보 |
| INFO | 프로그램 시작/종료, 눈 감기/뜸, 입 벌림 시작 |
| WARNING | 졸림 감지, 하품 감지, 경고음 재생 |
| ERROR | 카메라 오류, 모델 파일 없음 |

### 로그 예시
```
06:06:01.497 [INFO] 모델 로딩 중...
06:06:02.717 [INFO] 모델 로딩 완료!
06:06:05.941 [INFO] 카메라 연결 완료! (해상도: 640x480)
06:06:06.002 [DEBUG] EAR=0.170 (threshold=0.22), MAR=0.393 (threshold=0.6)
06:06:06.002 [INFO] 눈 감기 시작 - EAR: 0.170
06:06:08.306 [WARNING] 하품 감지! - MAR: 1.638
06:06:58.538 [WARNING] 졸림 감지! - 2.0초 경과, EAR: 0.139
```

## 종료

다음 방법으로 프로그램을 종료할 수 있습니다:

| 방법 | 설명 |
|-----|------|
| `ESC` 키 | 카메라 창에서 ESC 키 입력 |
| `q` 키 | 카메라 창에서 q 키 입력 |
| `Ctrl + C` | 터미널에서 인터럽트 |

> **Note**: macOS에서 OpenCV 창의 빨간 닫기(X) 버튼은 비활성화되어 있습니다. 이는 OpenCV의 macOS 백엔드 제한사항입니다. ESC 또는 q 키를 사용해 주세요.
