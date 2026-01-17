"""
졸림 감지 Webhook 전송 예제
===========================
졸림/하품 감지 시 외부 서버로 HTTP 요청을 보내는 예제입니다.
Slack, Discord, 또는 자체 서버로 알림을 전송할 수 있습니다.

사용법:
1. 터미널 1에서 main.py 실행
2. 터미널 2에서 이 스크립트 실행
"""

import os
import json
import urllib.request
from datetime import datetime

PIPE_PATH = "/tmp/face_status_pipe"

# Webhook URL 설정 (실제 사용 시 변경 필요)
SLACK_WEBHOOK_URL = None  # "https://hooks.slack.com/services/xxx/yyy/zzz"
DISCORD_WEBHOOK_URL = None  # "https://discord.com/api/webhooks/xxx/yyy"
CUSTOM_WEBHOOK_URL = None  # "https://your-server.com/api/drowsy-alert"


def send_slack_webhook(event_type, timestamp):
    """Slack으로 알림 전송"""
    if not SLACK_WEBHOOK_URL:
        print("  [Slack] URL 미설정 - 건너뜀")
        return

    emoji = "😴" if event_type == "DROWSY" else "🥱"
    message = "졸림이 감지되었습니다!" if event_type == "DROWSY" else "하품이 감지되었습니다!"

    payload = {
        "text": f"{emoji} *{message}*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{message}*\n시간: {timestamp}"
                }
            }
        ]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(SLACK_WEBHOOK_URL, data=data)
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=5)
        print("  [Slack] 전송 성공")
    except Exception as e:
        print(f"  [Slack] 전송 실패: {e}")


def send_discord_webhook(event_type, timestamp):
    """Discord로 알림 전송"""
    if not DISCORD_WEBHOOK_URL:
        print("  [Discord] URL 미설정 - 건너뜀")
        return

    emoji = "😴" if event_type == "DROWSY" else "🥱"
    title = "졸림 감지!" if event_type == "DROWSY" else "하품 감지!"
    color = 0xFF0000 if event_type == "DROWSY" else 0xFFA500

    payload = {
        "embeds": [{
            "title": f"{emoji} {title}",
            "description": f"시간: {timestamp}",
            "color": color
        }]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data)
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=5)
        print("  [Discord] 전송 성공")
    except Exception as e:
        print(f"  [Discord] 전송 실패: {e}")


def send_custom_webhook(event_type, timestamp):
    """커스텀 서버로 알림 전송"""
    if not CUSTOM_WEBHOOK_URL:
        print("  [Custom] URL 미설정 - 건너뜀")
        return

    payload = {
        "event": event_type,
        "timestamp": timestamp,
        "device": "MacBook",
        "source": "FacialExpressions"
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(CUSTOM_WEBHOOK_URL, data=data)
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=5)
        print("  [Custom] 전송 성공")
    except Exception as e:
        print(f"  [Custom] 전송 실패: {e}")


def on_event(event_type):
    """이벤트 발생 시 모든 웹훅으로 전송"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n[{timestamp}] {event_type} 이벤트 수신")
    print("웹훅 전송 중...")

    send_slack_webhook(event_type, timestamp)
    send_discord_webhook(event_type, timestamp)
    send_custom_webhook(event_type, timestamp)


def main():
    print("╔══════════════════════════════════════╗")
    print("║    졸림 감지 Webhook 전송 예제       ║")
    print("╚══════════════════════════════════════╝")
    print()
    print("웹훅 설정 상태:")
    print(f"  Slack:   {'설정됨' if SLACK_WEBHOOK_URL else '미설정'}")
    print(f"  Discord: {'설정됨' if DISCORD_WEBHOOK_URL else '미설정'}")
    print(f"  Custom:  {'설정됨' if CUSTOM_WEBHOOK_URL else '미설정'}")
    print()
    print("웹훅을 사용하려면 스크립트 상단의 URL을 설정하세요.")
    print()
    print(f"파이프 경로: {PIPE_PATH}")
    print("main.py를 먼저 실행하세요!")
    print("-" * 40)

    with open(PIPE_PATH, 'r') as pipe:
        while True:
            event = pipe.readline().strip()
            if event in ("DROWSY", "YAWN"):
                on_event(event)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("오류: Named Pipe를 찾을 수 없습니다.")
        print("main.py를 먼저 실행하세요.")
    except KeyboardInterrupt:
        print("\n\n프로그램 종료")
