"""
얼굴 표정 인식 및 졸림 감지 프로그램
- MediaPipe Face Landmarker로 얼굴/표정 인식
- EAR/MAR + 블렌드셰이프 기반 졸림 및 하품 감지
"""

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import os
import subprocess
import time
import stat
import logging
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 로그 설정
LOG_DIR = SCRIPT_DIR
LOG_FILE = os.path.join(LOG_DIR, f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 포맷터
formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

# 파일 핸들러 (즉시 쓰기를 위해 open으로 직접 생성)
file_handler = logging.FileHandler(LOG_FILE, mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 콘솔 핸들러
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

# 핸들러 추가
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# 로그 즉시 기록을 위한 래퍼 함수
_original_handle = logger.handle
def _flush_handle(record):
    _original_handle(record)
    file_handler.flush()
logger.handle = _flush_handle

# Named Pipe 경로
PIPE_PATH = "/tmp/face_status_pipe"

# 설정값
EAR_THRESHOLD = 0.22          # 눈 감김 판단 임계값 (MediaPipe 랜드마크 기반)
MAR_THRESHOLD = 0.6           # 하품 판단 임계값 (MediaPipe 랜드마크 기반)
BLINK_SCORE_THRESHOLD = 0.45  # 블렌드셰이프 eyeBlink 스코어 임계값
JAW_OPEN_SCORE_THRESHOLD = 0.35  # 블렌드셰이프 jawOpen 스코어 임계값
DROWSY_TIME = 2.0             # 졸림 판단 시간 (초)
YAWN_TIME = 1.0               # 하품 판단 시간 (초)
ALERT_COOLDOWN = 3.0          # 경고음 재생 간격 (초)
BLENDSHAPE_TOP_K = 3          # 화면에 표시할 상위 블렌드셰이프 개수

# MediaPipe 모델 경로
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
FACE_LANDMARKER_MODEL = os.path.join(MODELS_DIR, "face_landmarker.task")

# MediaPipe Face Landmarker에서 사용할 주요 랜드마크 인덱스
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
MOUTH_INDICES = {
    "left": 61,
    "right": 291,
    "upper": 13,
    "lower": 14,
    "upper_left": 81,
    "upper_right": 311,
    "lower_left": 178,
    "lower_right": 402,
}


def euclidean_distance(p1, p2):
    return float(np.linalg.norm(p1 - p2))


def eye_aspect_ratio(eye_points):
    """
    EAR (Eye Aspect Ratio) 계산
    눈의 세로/가로 비율로 눈 감김 정도 측정
    """
    A = euclidean_distance(eye_points[1], eye_points[5])
    B = euclidean_distance(eye_points[2], eye_points[4])
    C = euclidean_distance(eye_points[0], eye_points[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)


def mouth_aspect_ratio(mouth_points):
    """
    MAR (Mouth Aspect Ratio) 계산
    MediaPipe 얼굴 랜드마크로 하품 감지
    """
    A = euclidean_distance(mouth_points["upper"], mouth_points["lower"])
    B = euclidean_distance(mouth_points["upper_left"], mouth_points["lower_left"])
    C = euclidean_distance(mouth_points["upper_right"], mouth_points["lower_right"])
    D = euclidean_distance(mouth_points["left"], mouth_points["right"])
    if D == 0:
        return 0.0
    return (A + B + C) / (3.0 * D)


def to_pixel_landmarks(face_landmarks, image_shape):
    """정규화된 MediaPipe 랜드마크를 픽셀 좌표 dict로 변환"""
    height, width = image_shape[:2]
    return {
        idx: np.array([lm.x * width, lm.y * height], dtype=np.float32)
        for idx, lm in enumerate(face_landmarks)
    }


def load_face_landmarker(model_path):
    """MediaPipe Face Landmarker 모델 로드"""
    options = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=model_path),
        output_face_blendshapes=True,
        num_faces=1,
        running_mode=vision.RunningMode.VIDEO,
    )
    return vision.FaceLandmarker.create_from_options(options)


def build_blendshape_map(result):
    """blendshape 결과를 dict로 변환"""
    if not result.face_blendshapes:
        return {}
    first = result.face_blendshapes[0]
    categories = first.categories if hasattr(first, "categories") else first
    return {c.category_name: c.score for c in categories}


def summarize_emotion(blendshape_scores):
    """
    주요 표정 신호를 단순 매핑 (happy/frown/surprise/neutral)
    MediaPipe blendshape 조합을 간략한 레이블로 변환
    """
    smile = np.mean([
        blendshape_scores.get("mouthSmileLeft", 0.0),
        blendshape_scores.get("mouthSmileRight", 0.0),
    ])
    frown = np.mean([
        blendshape_scores.get("mouthFrownLeft", 0.0),
        blendshape_scores.get("mouthFrownRight", 0.0),
        blendshape_scores.get("browDownLeft", 0.0),
        blendshape_scores.get("browDownRight", 0.0),
    ])
    surprise = np.mean([
        blendshape_scores.get("jawOpen", 0.0),
        blendshape_scores.get("eyeWideLeft", 0.0),
        blendshape_scores.get("eyeWideRight", 0.0),
    ])
    neutral = blendshape_scores.get("mouthClose", 0.0)

    scores = {
        "happy": smile,
        "frown": frown,
        "surprise": surprise,
        "neutral": neutral,
    }
    label = max(scores, key=scores.get)
    return label, scores[label]


def play_alert_sound():
    """macOS 시스템 경고음 재생"""
    subprocess.Popen(
        ['afplay', '/System/Library/Sounds/Sosumi.aiff'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def find_builtin_camera():
    """
    맥북 빌트인 카메라를 찾아 인덱스 반환
    연속성 카메라(iPhone)보다 빌트인 카메라를 우선 사용
    """
    try:
        import AVFoundation
        logger.info("카메라 검색 중...")

        devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(
            AVFoundation.AVMediaTypeVideo
        )

        builtin_index = None
        # 빌트인 카메라 키워드: FaceTime, MacBook, Built-in
        builtin_keywords = ["FaceTime", "MacBook", "Built-in"]
        # 외장 카메라 키워드 (제외)
        external_keywords = ["iPhone", "iPad", "Continuity"]

        for i, device in enumerate(devices):
            name = device.localizedName()
            logger.debug(f"  카메라 {i}: {name}")

            # 외장 카메라 제외
            is_external = any(kw in name for kw in external_keywords)
            is_builtin = any(kw in name for kw in builtin_keywords)

            if not is_external and (is_builtin or builtin_index is None):
                if builtin_index is None:
                    builtin_index = i

        if builtin_index is not None:
            logger.info(f"빌트인 카메라 선택: 인덱스 {builtin_index}")
            return builtin_index
        elif devices:
            logger.info(f"기본 카메라 사용: 인덱스 0")
            return 0
        else:
            logger.warning("카메라를 찾을 수 없습니다.")
            return 0

    except ImportError:
        logger.debug("AVFoundation 모듈 없음 - 기본 카메라(인덱스 0) 사용")
        return 0


def setup_pipe():
    """Named Pipe 생성"""
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)
    os.mkfifo(PIPE_PATH, mode=stat.S_IRUSR | stat.S_IWUSR)
    logger.info(f"이벤트 파이프 생성: {PIPE_PATH}")


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
            logger.info("파이프 연결됨 (외부 수신자 감지)")

    if pipe_fd is None:
        return pipe_fd

    try:
        os.write(pipe_fd, f"{event_type}\n".encode())
    except (BrokenPipeError, BlockingIOError, OSError):
        pass  # 수신자가 없거나 버퍼가 찼으면 무시

    return pipe_fd


def main():
    # MediaPipe 모델 확인
    if not os.path.exists(FACE_LANDMARKER_MODEL):
        logger.error("MediaPipe Face Landmarker 모델 파일을 찾을 수 없습니다.")
        logger.error(f"경로: {FACE_LANDMARKER_MODEL}")
        logger.info("다음 명령으로 다운로드하세요:")
        logger.info(f"mkdir -p \"{MODELS_DIR}\"")
        logger.info("curl -L -o \"{model_path}\" https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task".format(
            model_path=FACE_LANDMARKER_MODEL))
        return

    # 초기화
    logger.info("MediaPipe Face Landmarker 로딩 중...")
    landmarker = load_face_landmarker(FACE_LANDMARKER_MODEL)
    logger.info("모델 로딩 완료!")

    # 졸림/하품 감지용 시간 기반 변수
    eye_closed_start = None  # 눈 감기 시작 시간
    yawn_start = None        # 하품 시작 시간
    last_alert_time = 0      # 마지막 경고음 시간
    is_drowsy = False        # 졸림 상태
    is_yawning = False       # 하품 상태
    current_ear = 0.0        # 현재 EAR 값
    current_mar = 0.0        # 현재 MAR 값
    blink_score = 0.0        # MediaPipe eyeBlink blendshape
    jaw_open_score = 0.0     # MediaPipe jawOpen blendshape
    top_blendshapes = []
    emotion_result = None

    # Named Pipe 설정 (non-blocking 쓰기 모드)
    setup_pipe()
    try:
        pipe_fd = os.open(PIPE_PATH, os.O_WRONLY | os.O_NONBLOCK)
        logger.info("파이프 연결됨 (외부 수신자 있음)")
    except OSError:
        pipe_fd = None
        logger.debug("파이프 수신자 없음 - 이벤트 전송 비활성화")

    # 카메라 시작 (빌트인 카메라 우선)
    camera_index = find_builtin_camera()

    # 기본 백엔드로 시도 (AVFoundation 명시 제거)
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error("카메라를 열 수 없습니다.")
        logger.error("macOS 시스템 설정 > 개인정보 보호 및 보안 > 카메라에서 터미널 접근을 허용해주세요.")
        return

    # 카메라 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # 카메라 워밍업 (첫 프레임 안정화 대기)
    logger.info("카메라 초기화 중...")
    time.sleep(1.0)

    # 버퍼 비우기
    for _ in range(30):
        cap.grab()

    ret, frame = cap.read()
    if not ret or frame is None:
        logger.error("카메라에서 프레임을 읽을 수 없습니다.")
        cap.release()
        return

    logger.info(f"카메라 연결 완료! (해상도: {frame.shape[1]}x{frame.shape[0]})")
    logger.info("=== 얼굴 표정 인식 시작 ===")
    logger.info("종료: ESC, q, 창 닫기, 또는 Ctrl+C")

    # 창 생성 (WINDOW_NORMAL로 X 버튼 활성화)
    window_name = 'Facial Expression & Drowsiness Detection'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("프레임을 읽을 수 없습니다.")
            break

        # 좌우 반전 (거울 모드)
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

        faces = result.face_landmarks if result else []

        if faces:
            face_landmarks = faces[0]
            pixel_landmarks = to_pixel_landmarks(face_landmarks, frame.shape)

            left_eye = np.array([pixel_landmarks[i] for i in LEFT_EYE_INDICES], dtype=np.float32)
            right_eye = np.array([pixel_landmarks[i] for i in RIGHT_EYE_INDICES], dtype=np.float32)
            mouth_points = {name: pixel_landmarks[idx] for name, idx in MOUTH_INDICES.items()}

            # EAR/MAR 계산
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            current_ear = (left_ear + right_ear) / 2.0
            current_mar = mouth_aspect_ratio(mouth_points)

            blendshape_scores = build_blendshape_map(result)
            blink_score = np.mean([
                blendshape_scores.get("eyeBlinkLeft", 0.0),
                blendshape_scores.get("eyeBlinkRight", 0.0),
            ])
            jaw_open_score = blendshape_scores.get("jawOpen", 0.0)

            # 간헐적 디버그 로그
            if frame_count % 10 == 0:
                logger.debug(
                    f"EAR={current_ear:.3f} (<{EAR_THRESHOLD}), "
                    f"MAR={current_mar:.3f} (> {MAR_THRESHOLD}), "
                    f"blink={blink_score:.2f} (> {BLINK_SCORE_THRESHOLD}), "
                    f"jawOpen={jaw_open_score:.2f} (> {JAW_OPEN_SCORE_THRESHOLD})"
                )

            # 표정 요약 및 상위 블렌드셰이프
            if blendshape_scores:
                emotion_result = summarize_emotion(blendshape_scores)
                top_blendshapes = sorted(blendshape_scores.items(), key=lambda kv: kv[1], reverse=True)[:BLENDSHAPE_TOP_K]
            else:
                emotion_result = None
                top_blendshapes = []

            # 얼굴 윤곽 및 랜드마크 표시
            xs = [pt[0] for pt in pixel_landmarks.values()]
            ys = [pt[1] for pt in pixel_landmarks.values()]
            x_min, x_max = int(np.min(xs)), int(np.max(xs))
            y_min, y_max = int(np.min(ys)), int(np.max(ys))
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            cv2.polylines(frame, [np.int32(left_eye)], True, (0, 255, 255), 1)
            cv2.polylines(frame, [np.int32(right_eye)], True, (0, 255, 255), 1)
            mouth_poly = np.array([
                mouth_points["left"],
                mouth_points["upper_left"],
                mouth_points["upper"],
                mouth_points["upper_right"],
                mouth_points["right"],
                mouth_points["lower_right"],
                mouth_points["lower"],
                mouth_points["lower_left"],
            ], dtype=np.int32)
            cv2.polylines(frame, [mouth_poly], True, (0, 255, 255), 1)

        else:
            # 얼굴이 감지되지 않으면 상태 리셋
            eye_closed_start = None
            yawn_start = None
            is_drowsy = False
            is_yawning = False
            current_ear = 0.0
            current_mar = 0.0
            blink_score = 0.0
            jaw_open_score = 0.0
            emotion_result = None
            top_blendshapes = []

        frame_count += 1

        # 졸림/하품 판단 (MediaPipe + EAR/MAR 결합)
        eye_closed_now = faces and (
            (current_ear > 0 and current_ear < EAR_THRESHOLD) or (blink_score >= BLINK_SCORE_THRESHOLD)
        )
        mouth_open_now = faces and (
            (current_mar > MAR_THRESHOLD) or (jaw_open_score >= JAW_OPEN_SCORE_THRESHOLD)
        )

        current_time = time.time()

        if eye_closed_now:
            if eye_closed_start is None:
                eye_closed_start = current_time
                logger.info(f"눈 감기 시작 - EAR: {current_ear:.3f}, blink: {blink_score:.2f}")
            elif current_time - eye_closed_start >= DROWSY_TIME:
                if not is_drowsy:
                    logger.warning(
                        f"졸림 감지! - {DROWSY_TIME}초 경과, EAR: {current_ear:.3f}, blink: {blink_score:.2f}"
                    )
                    pipe_fd = send_event(pipe_fd, "DROWSY")
                is_drowsy = True
        else:
            if eye_closed_start is not None:
                duration = current_time - eye_closed_start
                logger.info(
                    f"눈 뜸 - EAR: {current_ear:.3f}, blink: {blink_score:.2f}, 감은 시간: {duration:.2f}초"
                )
            eye_closed_start = None
            is_drowsy = False

        if mouth_open_now:
            if yawn_start is None:
                yawn_start = current_time
                logger.info(f"입 벌림 시작 - MAR: {current_mar:.3f}, jawOpen: {jaw_open_score:.2f}")
            elif current_time - yawn_start >= YAWN_TIME:
                if not is_yawning:
                    logger.warning(f"하품 감지! - MAR: {current_mar:.3f}, jawOpen: {jaw_open_score:.2f}")
                    pipe_fd = send_event(pipe_fd, "YAWN")
                is_yawning = True
        else:
            yawn_start = None
            is_yawning = False

        # 결과 표시 영역 (화면 왼쪽 상단)
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (340, 330), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        y_pos = 35
        cv2.putText(frame, "=== Status ===", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # EAR/MAR 표시
        y_pos += 25
        ear_color = (0, 0, 255) if current_ear < EAR_THRESHOLD else (200, 200, 200)
        cv2.putText(frame, f"EAR: {current_ear:.2f} (< {EAR_THRESHOLD})", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, ear_color, 1)
        y_pos += 20
        mar_color = (0, 0, 255) if current_mar > MAR_THRESHOLD else (200, 200, 200)
        cv2.putText(frame, f"MAR: {current_mar:.2f} (> {MAR_THRESHOLD})", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, mar_color, 1)
        y_pos += 20
        blink_color = (0, 0, 255) if blink_score >= BLINK_SCORE_THRESHOLD else (200, 200, 200)
        cv2.putText(frame, f"Blink: {blink_score:.2f} (> {BLINK_SCORE_THRESHOLD})", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, blink_color, 1)
        y_pos += 20
        jaw_color = (0, 0, 255) if jaw_open_score >= JAW_OPEN_SCORE_THRESHOLD else (200, 200, 200)
        cv2.putText(frame, f"JawOpen: {jaw_open_score:.2f} (> {JAW_OPEN_SCORE_THRESHOLD})", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, jaw_color, 1)

        # 눈 감은 시간 표시
        y_pos += 20
        if eye_closed_start is not None:
            closed_duration = time.time() - eye_closed_start
            cv2.putText(frame, f"Eyes closed: {closed_duration:.1f}s / {DROWSY_TIME:.1f}s", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        else:
            cv2.putText(frame, "Eyes: Open", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        # 졸림/하품 상태 표시
        y_pos += 25
        if is_drowsy:
            cv2.putText(frame, "DROWSY!", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Drowsy: No", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        y_pos += 25
        if is_yawning:
            cv2.putText(frame, "YAWNING!", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        else:
            cv2.putText(frame, "Yawn: No", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        # 표정 결과 표시
        y_pos += 30
        cv2.putText(frame, "=== Emotion ===", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        if emotion_result:
            label, confidence = emotion_result
            y_pos += 25
            color = (0, 255, 0) if confidence > 0.5 else (0, 255, 255)
            cv2.putText(frame, f"{label}: {confidence*100:.1f}%", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        if top_blendshapes:
            y_pos += 22
            cv2.putText(frame, "Top blendshapes:", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            for name, score in top_blendshapes:
                y_pos += 18
                cv2.putText(frame, f"- {name}: {score:.2f}", (20, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1)

        # 경고 알림 (화면 중앙 상단) + 경고음
        current_time = time.time()
        if is_drowsy or is_yawning:
            # 화면 중앙 상단에 Wake up 경고
            text = "Wake up!"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            text_x = (frame.shape[1] - text_size[0]) // 2
            cv2.putText(frame, text, (text_x, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            # 경고음 재생 (쿨다운 적용)
            if current_time - last_alert_time > ALERT_COOLDOWN:
                play_alert_sound()
                last_alert_time = current_time
                logger.warning(f"경고음 재생 - 졸림:{is_drowsy}, 하품:{is_yawning}")

        # 화면 출력
        cv2.imshow(window_name, frame)

        # 종료 조건 확인 (ESC키, q키, 또는 창 닫기)
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):  # ESC 또는 q
            logger.info("키 입력으로 종료")
            break

        # 창이 닫혔는지 확인 (X 버튼 클릭)
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            logger.info("창 닫기로 종료")
            break

    # 정리
    cap.release()
    cv2.destroyAllWindows()
    if pipe_fd is not None:
        os.close(pipe_fd)
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)
    logger.info("프로그램 종료")
    logger.info(f"로그 파일 저장됨: {LOG_FILE}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Ctrl+C 감지 - 프로그램 종료")
        cv2.destroyAllWindows()
    finally:
        logging.shutdown()
