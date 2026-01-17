"""
졸림 감지 자동화 예제
=====================
졸림/하품 감지 시 자동으로 특정 작업을 수행하는 예제입니다.
- 화면 밝기 조절
- 음악 재생/정지
- 애플리케이션 제어

사용법:
1. 터미널 1에서 main.py 실행
2. 터미널 2에서 이 스크립트 실행
"""

import os
import subprocess
from datetime import datetime

PIPE_PATH = "/tmp/face_status_pipe"


def set_screen_brightness(level):
    """
    화면 밝기 조절 (0.0 ~ 1.0)
    주의: brightness 명령어가 필요합니다
    설치: brew install brightness
    """
    try:
        subprocess.run(['brightness', str(level)], capture_output=True, timeout=5)
        print(f"  화면 밝기: {int(level * 100)}%")
    except FileNotFoundError:
        print("  [밝기 조절 불가] 'brew install brightness'로 설치하세요")
    except Exception as e:
        print(f"  밝기 조절 실패: {e}")


def control_music(action):
    """
    음악 재생 제어 (Music 앱)
    action: 'play', 'pause', 'next'
    """
    script = f'tell application "Music" to {action}'
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        print(f"  Music 앱: {action}")
    except Exception as e:
        print(f"  Music 제어 실패: {e}")


def pause_video():
    """동영상 재생 일시정지 (스페이스바 시뮬레이션)"""
    script = '''
    tell application "System Events"
        key code 49
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        print("  스페이스바 전송 (동영상 일시정지)")
    except Exception as e:
        print(f"  키 전송 실패: {e}")


def speak_alert(message):
    """TTS로 경고 메시지 음성 출력"""
    try:
        subprocess.Popen(
            ['say', '-v', 'Yuna', message],  # Yuna: 한국어 음성
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"  음성 출력: {message}")
    except Exception as e:
        print(f"  음성 출력 실패: {e}")


def open_app(app_name):
    """애플리케이션 실행"""
    try:
        subprocess.run(['open', '-a', app_name], capture_output=True, timeout=5)
        print(f"  앱 실행: {app_name}")
    except Exception as e:
        print(f"  앱 실행 실패: {e}")


def lock_screen():
    """화면 잠금"""
    script = 'tell application "System Events" to keystroke "q" using {command down, control down}'
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        print("  화면 잠금 실행")
    except Exception as e:
        print(f"  화면 잠금 실패: {e}")


def on_drowsy(count):
    """졸림 감지 시 자동화 작업"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 졸림 감지 #{count}")
    print("자동화 작업 실행 중...")

    # 1. 음성 경고
    speak_alert("졸리시면 잠시 쉬세요")

    # 2. 음악 일시정지 (재생 중이라면)
    control_music("pause")

    # 3. 화면 밝기 올리기
    set_screen_brightness(1.0)

    # 4. 3번 이상 졸리면 강제 휴식 권유
    if count >= 3:
        print("\n⚠️ 3회 이상 졸림 감지 - 강제 휴식 권유!")
        speak_alert("지금 바로 10분간 휴식하세요")
        # lock_screen()  # 필요시 주석 해제


def on_yawn(count):
    """하품 감지 시 자동화 작업"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 하품 감지 #{count}")
    print("자동화 작업 실행 중...")

    # 1. 음성 안내
    speak_alert("하품이 나왔네요. 스트레칭하세요")

    # 5번 이상 하품하면 휴식 권유
    if count >= 5:
        print("\n💤 5회 이상 하품 - 피로 누적!")
        speak_alert("많이 피곤하신 것 같아요. 잠시 쉬어가세요")


def main():
    print("╔══════════════════════════════════════╗")
    print("║    졸림 감지 자동화 예제             ║")
    print("╚══════════════════════════════════════╝")
    print()
    print("자동화 기능:")
    print("  - 졸림 감지 시: 음성 경고, 음악 정지, 화면 밝기 UP")
    print("  - 하품 감지 시: 음성 안내")
    print("  - 3회 이상 졸림: 강제 휴식 권유")
    print("  - 5회 이상 하품: 피로 경고")
    print()
    print(f"파이프 경로: {PIPE_PATH}")
    print("main.py를 먼저 실행하세요!")
    print("-" * 50)

    drowsy_count = 0
    yawn_count = 0

    with open(PIPE_PATH, 'r') as pipe:
        while True:
            event = pipe.readline().strip()
            if event == "DROWSY":
                drowsy_count += 1
                on_drowsy(drowsy_count)
            elif event == "YAWN":
                yawn_count += 1
                on_yawn(yawn_count)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("오류: Named Pipe를 찾을 수 없습니다.")
        print("main.py를 먼저 실행하세요.")
    except KeyboardInterrupt:
        print("\n\n프로그램 종료")
