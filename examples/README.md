# 외부 프로그램 연동 예제

main.py에서 발생하는 졸림/하품 이벤트를 외부 프로그램에서 수신하는 다양한 예제입니다.

## 사용 방법

```bash
# 터미널 1: 얼굴 인식 프로그램 실행
python main.py

# 터미널 2: 예제 스크립트 실행 (아래 중 하나 선택)
python examples/drowsy_alert_example.py
```

## 예제 목록

### 1. 기본 알림 예제 (`drowsy_alert_example.py`)

가장 기본적인 예제로, 졸림/하품 감지 시:
- macOS 시스템 사운드 재생
- macOS 알림 센터에 알림 표시
- 이벤트 로그 파일 저장

```bash
python examples/drowsy_alert_example.py
```

### 2. Webhook 전송 예제 (`drowsy_webhook_example.py`)

외부 서버로 HTTP 요청을 전송하는 예제:
- Slack 웹훅
- Discord 웹훅
- 커스텀 서버 API

```bash
# 스크립트 상단의 WEBHOOK_URL 변수를 설정 후 실행
python examples/drowsy_webhook_example.py
```

### 3. 자동화 예제 (`drowsy_automation_example.py`)

시스템 자동화 기능 예제:
- 화면 밝기 조절
- 음악 재생/정지 (Music 앱)
- TTS 음성 경고
- 동영상 일시정지
- 반복 졸림 시 강제 휴식 권유

```bash
python examples/drowsy_automation_example.py
```

### 4. 통계 수집 예제 (`drowsy_statistics_example.py`)

이벤트 통계를 수집하고 분석하는 예제:
- 세션별 통계
- 시간대별 이벤트 분포
- 피로도 분석
- JSON 파일로 데이터 저장

```bash
python examples/drowsy_statistics_example.py
```

## 이벤트 종류

| 이벤트 | 설명 |
|-------|------|
| `DROWSY` | 졸림 감지 (눈 2초 이상 감음) |
| `YAWN` | 하품 감지 (입 1초 이상 벌림) |

## 직접 구현하기

Named Pipe를 통해 이벤트를 수신하는 기본 코드:

```python
PIPE_PATH = "/tmp/face_status_pipe"

with open(PIPE_PATH, 'r') as pipe:
    while True:
        event = pipe.readline().strip()
        if event == "DROWSY":
            # 졸림 감지 시 처리
            print("졸림 감지!")
        elif event == "YAWN":
            # 하품 감지 시 처리
            print("하품 감지!")
```

## 다른 언어로 구현

### Shell Script

```bash
#!/bin/bash
PIPE_PATH="/tmp/face_status_pipe"

while read event; do
    if [ "$event" = "DROWSY" ]; then
        echo "졸림 감지!"
        # 처리 로직
    elif [ "$event" = "YAWN" ]; then
        echo "하품 감지!"
        # 처리 로직
    fi
done < "$PIPE_PATH"
```

### Node.js

```javascript
const fs = require('fs');
const PIPE_PATH = '/tmp/face_status_pipe';

const pipe = fs.createReadStream(PIPE_PATH, { encoding: 'utf8' });

pipe.on('data', (data) => {
    const events = data.trim().split('\n');
    events.forEach(event => {
        if (event === 'DROWSY') {
            console.log('졸림 감지!');
        } else if (event === 'YAWN') {
            console.log('하품 감지!');
        }
    });
});
```

### Go

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
        event := scanner.Text()
        switch event {
        case "DROWSY":
            fmt.Println("졸림 감지!")
        case "YAWN":
            fmt.Println("하품 감지!")
        }
    }
}
```
