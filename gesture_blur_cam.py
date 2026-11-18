"""
==================================================
TrendBlur v3.0
Gesture Controlled Camera Blur
Python 3.11
MediaPipe Tasks
==================================================

Gesture:
    ✌️  -> BLUR
    Normal -> NORMAL

Q -> Keluar
"""

import os
import time

import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ==================================================
# CONFIGURATION
# ==================================================

MODEL_PATH = "hand_landmarker.task"

CAMERA_WIDTH = 700
CAMERA_HEIGHT = 500

MAX_HANDS = 2

MIN_DETECTION = 0.5
MIN_PRESENCE = 0.5
MIN_TRACKING = 0.5

BLUR_MAX_KERNEL = 81

SMOOTHING = 0.15


# ==================================================
# HAND CONNECTIONS
# ==================================================

HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),

    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),

    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),

    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),

    (13, 17),

    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
]


# ==================================================
# CHECK MODEL
# ==================================================

def check_model():

    if not os.path.isfile(MODEL_PATH):

        raise FileNotFoundError(
            "\n"
            "Model hand_landmarker.task tidak ditemukan.\n\n"
            "Pastikan file berada di folder:\n"
            f"{os.path.abspath(MODEL_PATH)}\n"
        )

    size = os.path.getsize(MODEL_PATH)

    if size < 100000:

        raise RuntimeError(
            "File hand_landmarker.task terlalu kecil "
            "atau kemungkinan rusak."
        )

    print(f"Model ditemukan: {MODEL_PATH}")
    print(f"Ukuran model : {size / (1024 * 1024):.2f} MB")


# ==================================================
# BLUR
# ==================================================

def apply_blur(frame, strength):

    if strength <= 0:
        return frame

    kernel = int(strength * BLUR_MAX_KERNEL)

    kernel = max(kernel, 1)

    if kernel % 2 == 0:
        kernel += 1

    return cv2.GaussianBlur(
        frame,
        (kernel, kernel),
        0
    )


# ==================================================
# DRAW HAND
# ==================================================

def draw_hand(frame, landmarks):

    height, width, _ = frame.shape

    # Lines
    for start, end in HAND_CONNECTIONS:

        p1 = landmarks[start]
        p2 = landmarks[end]

        x1 = int(p1.x * width)
        y1 = int(p1.y * height)

        x2 = int(p2.x * width)
        y2 = int(p2.y * height)

        cv2.line(
            frame,
            (x1, y1),
            (x2, y2),
            (220, 220, 220),
            2
        )

    # Points
    for landmark in landmarks:

        x = int(landmark.x * width)
        y = int(landmark.y * height)

        cv2.circle(
            frame,
            (x, y),
            5,
            (0, 255, 0),
            -1
        )


# ==================================================
# PEACE GESTURE
# ==================================================

def is_peace(landmarks):

    # INDEX
    index_up = (
        landmarks[8].y <
        landmarks[6].y
    )

    # MIDDLE
    middle_up = (
        landmarks[12].y <
        landmarks[10].y
    )

    # RING
    ring_down = (
        landmarks[16].y >
        landmarks[14].y
    )

    # PINKY
    pinky_down = (
        landmarks[20].y >
        landmarks[18].y
    )

    return (
        index_up
        and middle_up
        and ring_down
        and pinky_down
    )


# ==================================================
# FPS
# ==================================================

class FPS:

    def __init__(self):

        self.previous_time = time.time()
        self.value = 0

    def update(self):

        current_time = time.time()

        delta = current_time - self.previous_time

        self.previous_time = current_time

        if delta > 0:
            self.value = 1 / delta

        return int(self.value)


# ==================================================
# CREATE MEDIAPIPE LANDMARKER
# ==================================================

def create_landmarker():

    print("Membuat MediaPipe Hand Landmarker...")

    base_options = python.BaseOptions(
        model_asset_path=os.path.abspath(MODEL_PATH)
    )

    options = vision.HandLandmarkerOptions(

        base_options=base_options,

        running_mode=vision.RunningMode.IMAGE,

        num_hands=MAX_HANDS,

        min_hand_detection_confidence=MIN_DETECTION,

        min_hand_presence_confidence=MIN_PRESENCE,

        min_tracking_confidence=MIN_TRACKING,
    )

    return vision.HandLandmarker.create_from_options(
        options
    )


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 50)
    print("TrendBlur v3.0")
    print("Gesture Controlled Camera Blur")
    print("=" * 50)

    # Check model
    check_model()

    # Camera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        raise RuntimeError(
            "Tidak dapat membuka kamera."
        )

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    fps_counter = FPS()

    blur_strength = 0.0

    target_blur = 0.0

    print()
    print("Camera berhasil dibuka.")
    print()
    print("Kontrol:")
    print("✌️  = BLUR")
    print("Tangan biasa = NORMAL")
    print("Q = Keluar")
    print()

    # Create MediaPipe
    with create_landmarker() as landmarker:

        while True:

            ret, frame = cap.read()

            if not ret:

                print(
                    "Gagal membaca frame kamera."
                )

                break

            # Mirror camera
            frame = cv2.flip(
                frame,
                1
            )

            # BGR -> RGB
            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            # MediaPipe image
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb
            )

            # Detect
            result = landmarker.detect(
                mp_image
            )

            peace_detected = False

            # Check hands
            if result.hand_landmarks:

                for hand in result.hand_landmarks:

                    if is_peace(hand):

                        peace_detected = True

            # Target blur
            target_blur = (
                1.0
                if peace_detected
                else 0.0
            )

            # Smooth transition
            blur_strength += (
                target_blur -
                blur_strength
            ) * SMOOTHING

            if blur_strength < 0.01:

                blur_strength = 0.0

            # Apply blur
            frame = apply_blur(
                frame,
                blur_strength
            )

            # Draw hands
            if result.hand_landmarks:

                for hand in result.hand_landmarks:

                    draw_hand(
                        frame,
                        hand
                    )

            # FPS
            fps = fps_counter.update()

            # Status
            if peace_detected:

                status = "BLUR ON"
                status_color = (
                    0,
                    0,
                    255
                )

            else:

                status = "NORMAL"
                status_color = (
                    0,
                    255,
                    0
                )

            # UI Background
            cv2.rectangle(

                frame,

                (10, 10),

                (270, 105),

                (30, 30, 30),

                -1
            )

            # Status
            cv2.putText(

                frame,

                f"Status : {status}",

                (20, 42),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                status_color,

                2
            )

            # FPS
            cv2.putText(

                frame,

                f"FPS : {fps}",

                (20, 72),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (255, 255, 255),

                2
            )

            # Gesture
            cv2.putText(

                frame,

                "Peace = Blur",

                (20, 97),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (220, 220, 220),

                1
            )

            # Show
            cv2.imshow(

                "TrendBlur v3.0",

                frame
            )

            # Keyboard
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                break

    # Cleanup
    cap.release()

    cv2.destroyAllWindows()

    print()
    print("TrendBlur selesai.")
    print()


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":

    main()
