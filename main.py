"""
얼굴 표정 인식 및 졸림 감지 프로그램
- FER 라이브러리로 7가지 표정 인식
- EAR/MAR로 졸림 및 하품 감지
"""

import cv2
import numpy as np
from fer.fer import FER
import dlib
from scipy.spatial import distance as dist
import os
import subprocess
import time
import stat

# Named Pipe 경로
PIPE_PATH = "/tmp/face_status_pipe"

# 설정값
EAR_THRESHOLD = 0.22  # 눈 감김 판단 임계값 (낮을수록 더 감아야 감지)
MAR_THRESHOLD = 0.6   # 하품 판단 임계값
DROWSY_TIME = 2.0     # 졸림 판단 시간 (초)
YAWN_TIME = 1.0       # 하품 판단 시간 (초)
ALERT_COOLDOWN = 3.0  # 경고음 재생 간격 (초)


def eye_aspect_ratio(eye_points):
    """
    EAR (Eye Aspect Ratio) 계산
    눈의 세로/가로 비율로 눈 감김 정도 측정
    """
    # 세로 거리 (2개)
    A = dist.euclidean(eye_points[1], eye_points[5])
    B = dist.euclidean(eye_points[2], eye_points[4])
    # 가로 거리 (1개)
    C = dist.euclidean(eye_points[0], eye_points[3])

    ear = (A + B) / (2.0 * C)
    return ear


def mouth_aspect_ratio(mouth_points):
    """
    MAR (Mouth Aspect Ratio) 계산
    입의 세로/가로 비율로 하품 감지
    """
    # 세로 거리 (3개)
    A = dist.euclidean(mouth_points[2], mouth_points[10])  # 51, 59
    B = dist.euclidean(mouth_points[4], mouth_points[8])   # 53, 57
    C = dist.euclidean(mouth_points[3], mouth_points[9])   # 52, 58
    # 가로 거리 (1개)
    D = dist.euclidean(mouth_points[0], mouth_points[6])   # 49, 55

    mar = (A + B + C) / (2.0 * D)
    return mar


def get_landmarks(predictor, gray, rect):
    """dlib으로 얼굴 랜드마크 68개 점 추출"""
    shape = predictor(gray, rect)
    coords = np.zeros((68, 2), dtype=int)
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords


def play_alert_sound():
    """macOS 시스템 경고음 재생"""
    subprocess.Popen(
        ['afplay', '/System/Library/Sounds/Sosumi.aiff'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def setup_pipe():
    """Named Pipe 생성"""
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)
    os.mkfifo(PIPE_PATH, mode=stat.S_IRUSR | stat.S_IWUSR)
    print(f"이벤트 파이프 생성: {PIPE_PATH}")


def try_connect_pipe():
    """파이프 연결 시도 (non-blocking)"""
    try:
        return os.open(PIPE_PATH, os.O_WRONLY | os.O_NONBLOCK)
    except OSError:
        return None


def send_event(pipe_fd, event_type):
    """파이프로 이벤트 전송 (non-blocking), 연결 안 됐으면 재시도"""
    # 연결 안 됐으면 재시도
    if pipe_fd is None:
        pipe_fd = try_connect_pipe()
        if pipe_fd is not None:
            print("파이프 연결됨 (외부 수신자 감지)")

    if pipe_fd is None:
        return pipe_fd

    try:
        os.write(pipe_fd, f"{event_type}\n".encode())
    except (BrokenPipeError, BlockingIOError, OSError):
        pass  # 수신자가 없거나 버퍼가 찼으면 무시

    return pipe_fd


def main():
    # 모델 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    landmark_path = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat")

    # 모델 파일 확인
    if not os.path.exists(landmark_path):
        print(f"오류: 랜드마크 모델 파일을 찾을 수 없습니다.")
        print(f"경로: {landmark_path}")
        print("다음 명령으로 다운로드하세요:")
        print("curl -L -o shape_predictor_68_face_landmarks.dat.bz2 http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        print("bunzip2 shape_predictor_68_face_landmarks.dat.bz2")
        return

    # 초기화
    print("모델 로딩 중...")
    emotion_detector = FER(mtcnn=True)
    face_detector = dlib.get_frontal_face_detector()
    landmark_predictor = dlib.shape_predictor(landmark_path)
    print("모델 로딩 완료!")

    # 눈, 입 랜드마크 인덱스 (dlib 68 랜드마크 기준)
    LEFT_EYE = list(range(36, 42))
    RIGHT_EYE = list(range(42, 48))
    MOUTH = list(range(48, 60))

    # 졸림/하품 감지용 시간 기반 변수
    eye_closed_start = None  # 눈 감기 시작 시간
    yawn_start = None        # 하품 시작 시간
    last_alert_time = 0      # 마지막 경고음 시간
    is_drowsy = False        # 졸림 상태
    is_yawning = False       # 하품 상태
    current_ear = 0          # 현재 EAR 값
    current_mar = 0          # 현재 MAR 값

    # Named Pipe 설정 (non-blocking 쓰기 모드)
    setup_pipe()
    try:
        pipe_fd = os.open(PIPE_PATH, os.O_WRONLY | os.O_NONBLOCK)
        print("파이프 연결됨 (외부 수신자 있음)")
    except OSError:
        pipe_fd = None
        print("파이프 수신자 없음 - 이벤트 전송 비활성화")

    # 카메라 시작
    print("카메라 연결 중...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("오류: 카메라를 열 수 없습니다.")
        print("macOS 시스템 설정 > 개인정보 보호 및 보안 > 카메라에서 터미널 접근을 허용해주세요.")
        return

    print("카메라 연결 완료!")
    print("\n=== 얼굴 표정 인식 시작 ===")
    print("종료: Ctrl + C")
    print("============================\n")

    frame_count = 0
    emotion_result = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다.")
            break

        # 좌우 반전 (거울 모드)
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # dlib으로 얼굴 감지
        faces = face_detector(gray)

        for face in faces:
            # 랜드마크 추출
            landmarks = get_landmarks(landmark_predictor, gray, face)

            # 눈 좌표 추출
            left_eye = landmarks[LEFT_EYE]
            right_eye = landmarks[RIGHT_EYE]
            mouth = landmarks[MOUTH]

            # EAR 계산
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            current_ear = (left_ear + right_ear) / 2.0

            # MAR 계산
            current_mar = mouth_aspect_ratio(mouth)

            current_time = time.time()

            # 졸림 판단 (시간 기반)
            if current_ear < EAR_THRESHOLD:
                if eye_closed_start is None:
                    eye_closed_start = current_time
                    print(f"[DEBUG] 눈 감기 시작 - EAR: {current_ear:.3f}")
                elif current_time - eye_closed_start >= DROWSY_TIME:
                    if not is_drowsy:
                        print(f"[DEBUG] 졸림 감지! - {DROWSY_TIME}초 경과")
                        pipe_fd = send_event(pipe_fd, "DROWSY")
                    is_drowsy = True
            else:
                if eye_closed_start is not None:
                    print(f"[DEBUG] 눈 뜸 - EAR: {current_ear:.3f}")
                eye_closed_start = None
                is_drowsy = False

            # 하품 판단 (시간 기반)
            if current_mar > MAR_THRESHOLD:
                if yawn_start is None:
                    yawn_start = current_time
                elif current_time - yawn_start >= YAWN_TIME:
                    if not is_yawning:
                        print(f"[DEBUG] 하품 감지!")
                        pipe_fd = send_event(pipe_fd, "YAWN")
                    is_yawning = True
            else:
                yawn_start = None
                is_yawning = False

            # 눈 랜드마크 그리기
            cv2.polylines(frame, [left_eye], True, (0, 255, 255), 1)
            cv2.polylines(frame, [right_eye], True, (0, 255, 255), 1)

            # 입 랜드마크 그리기
            cv2.polylines(frame, [mouth], True, (0, 255, 255), 1)

            # 얼굴 박스 그리기
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 얼굴이 감지되지 않으면 상태 리셋
        if not faces:
            eye_closed_start = None
            yawn_start = None
            is_drowsy = False
            is_yawning = False
            current_ear = 0
            current_mar = 0

        # 표정 인식 (매 5프레임마다 - 성능 최적화)
        frame_count += 1
        if frame_count % 5 == 0:
            emotions = emotion_detector.detect_emotions(frame)
            if emotions:
                emotion_result = emotions[0]

        # 결과 표시 영역 (화면 왼쪽 상단) - 2배 크기
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (640, 500), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        y_pos = 60
        cv2.putText(frame, "=== Status ===", (30, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        # EAR/MAR 표시
        y_pos += 50
        ear_color = (0, 0, 255) if current_ear < EAR_THRESHOLD else (200, 200, 200)
        cv2.putText(frame, f"EAR: {current_ear:.2f} (< {EAR_THRESHOLD})", (30, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, ear_color, 2)
        y_pos += 40
        cv2.putText(frame, f"MAR: {current_mar:.2f}", (30, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        # 눈 감은 시간 표시
        y_pos += 40
        if eye_closed_start is not None:
            closed_duration = time.time() - eye_closed_start
            cv2.putText(frame, f"Eyes closed: {closed_duration:.1f}s / {DROWSY_TIME:.1f}s", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        else:
            cv2.putText(frame, "Eyes: Open", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        # 졸림/하품 상태 표시
        y_pos += 50
        if is_drowsy:
            cv2.putText(frame, "DROWSY!", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
        else:
            cv2.putText(frame, "Drowsy: No", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        y_pos += 50
        if is_yawning:
            cv2.putText(frame, "YAWNING!", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 165, 255), 3)
        else:
            cv2.putText(frame, "Yawn: No", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # 표정 결과 표시
        y_pos += 60
        cv2.putText(frame, "=== Emotion ===", (30, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        if emotion_result:
            emotions = emotion_result['emotions']
            dominant = max(emotions, key=emotions.get)
            confidence = emotions[dominant]

            y_pos += 50
            color = (0, 255, 0) if confidence > 0.5 else (0, 255, 255)
            cv2.putText(frame, f"{dominant}: {confidence*100:.1f}%", (30, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        # 경고 알림 (화면 중앙 상단) + 경고음
        current_time = time.time()
        if is_drowsy or is_yawning:
            # 화면 중앙 상단에 Wake up 경고
            text = "Wake up!"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 3.0, 5)[0]
            text_x = (frame.shape[1] - text_size[0]) // 2
            cv2.putText(frame, text, (text_x, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0, 0, 255), 5)
            # 경고음 재생 (쿨다운 적용)
            if current_time - last_alert_time > ALERT_COOLDOWN:
                play_alert_sound()
                last_alert_time = current_time
                print(f"[경고] {'졸림' if is_drowsy else ''} {'하품' if is_yawning else ''} 감지!")

        # 화면 출력
        cv2.imshow('Facial Expression & Drowsiness Detection', frame)
        cv2.waitKey(1)

    # 정리
    cap.release()
    cv2.destroyAllWindows()
    if pipe_fd is not None:
        os.close(pipe_fd)
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)
    print("\n프로그램 종료")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCtrl+C 감지 - 프로그램 종료")
        cv2.destroyAllWindows()
