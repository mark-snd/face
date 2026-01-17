"""
졸림 감지 알림 수신 예제
========================
main.py에서 전송하는 졸림/하품 이벤트를 수신하여
다양한 알림 동작을 수행하는 예제입니다.

사용법:
1. 터미널 1에서 main.py 실행
2. 터미널 2에서 이 스크립트 실행
"""

import os
import subprocess
from datetime import datetime

PIPE_PATH = "/tmp/face_status_pipe"


def play_custom_sound(sound_name="Ping"):
    """macOS 시스템 사운드 재생"""
    sound_path = f"/System/Library/Sounds/{sound_name}.aiff"
    if os.path.exists(sound_path):
        subprocess.Popen(
            ['afplay', sound_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


def show_notification(title, message):
    """macOS 알림 센터에 알림 표시"""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(['osascript', '-e', script], capture_output=True)


def log_event(event_type):
    """이벤트를 파일에 기록"""
    log_file = "drowsy_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {event_type}\n")
    print(f"로그 저장: {log_file}")


def on_drowsy():
    """졸림 감지 시 처리"""
    print("=" * 50)
    print("⚠️  졸림 감지!")
    print("=" * 50)

    # 1. 경고음 재생
    play_custom_sound("Glass")

    # 2. 시스템 알림 표시
    show_notification("졸림 경고", "눈을 2초 이상 감았습니다. 잠시 휴식하세요!")

    # 3. 로그 기록
    log_event("DROWSY")


def on_yawn():
    """하품 감지 시 처리"""
    print("=" * 50)
    print("😮 하품 감지!")
    print("=" * 50)

    # 1. 경고음 재생
    play_custom_sound("Tink")

    # 2. 시스템 알림 표시
    show_notification("하품 감지", "하품이 감지되었습니다. 환기하거나 스트레칭하세요!")

    # 3. 로그 기록
    log_event("YAWN")


def main():
    print("╔══════════════════════════════════════╗")
    print("║    졸림 감지 알림 수신 프로그램      ║")
    print("╚══════════════════════════════════════╝")
    print()
    print(f"파이프 경로: {PIPE_PATH}")
    print("main.py를 먼저 실행하세요!")
    print()
    print("대기 중...")
    print("-" * 40)

    drowsy_count = 0
    yawn_count = 0

    with open(PIPE_PATH, 'r') as pipe:
        while True:
            event = pipe.readline().strip()
            if event:
                if event == "DROWSY":
                    drowsy_count += 1
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 졸림 #{drowsy_count}")
                    on_drowsy()

                elif event == "YAWN":
                    yawn_count += 1
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 하품 #{yawn_count}")
                    on_yawn()

                print(f"\n누적: 졸림 {drowsy_count}회 | 하품 {yawn_count}회")
                print("-" * 40)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("오류: Named Pipe를 찾을 수 없습니다.")
        print("main.py를 먼저 실행하세요.")
    except KeyboardInterrupt:
        print("\n\n프로그램 종료")
