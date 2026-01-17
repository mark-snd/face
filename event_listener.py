"""
졸림/하품 이벤트 수신 예제
main.py가 실행 중일 때 이 스크립트를 실행하세요.
"""

PIPE_PATH = "/tmp/face_status_pipe"

def main():
    print("이벤트 대기 중... (main.py를 먼저 실행하세요)")
    print(f"파이프: {PIPE_PATH}")
    print("-" * 40)

    with open(PIPE_PATH, 'r') as pipe:
        while True:
            event = pipe.readline().strip()
            if event:
                if event == "DROWSY":
                    print(f"[수신] 졸림 감지됨!")
                    # 여기에 졸림 감지 시 처리할 로직 추가
                elif event == "YAWN":
                    print(f"[수신] 하품 감지됨!")
                    # 여기에 하품 감지 시 처리할 로직 추가


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("오류: main.py를 먼저 실행하세요.")
    except KeyboardInterrupt:
        print("\n종료")
