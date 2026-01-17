# Facial Expression & Drowsiness Detection

실시간 얼굴 표정 인식 및 졸림/하품 감지 프로그램입니다.

## 주요 기능

- **표정 인식**: FER 라이브러리를 사용하여 7가지 표정 감지 (angry, disgust, fear, happy, sad, surprise, neutral)
- **졸림 감지**: EAR (Eye Aspect Ratio) 알고리즘으로 눈 감김 상태 측정
- **하품 감지**: MAR (Mouth Aspect Ratio) 알고리즘으로 하품 감지
- **실시간 경고**: 졸림/하품 감지 시 시각적 경고 및 macOS 시스템 경고음 재생
- **외부 연동**: Named Pipe를 통해 외부 프로그램에 이벤트 전송

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

```bash
python main.py
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

## 종료

`Ctrl + C` 또는 창 닫기
