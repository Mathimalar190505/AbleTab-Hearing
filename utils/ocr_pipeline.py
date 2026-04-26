"""
utils/ocr_pipeline.py - Webcam Capture + OCR (Clean Version)
"""

import cv2
import pytesseract
import os
import time
import numpy as np
import re

# ✅ Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------------------------------
# Configuration
# -----------------------------------------------

WEBCAM_INDEX = 0
CAPTURE_INTERVAL = 12
TESSERACT_CONFIG = "--oem 3 --psm 6 -l eng"

# -----------------------------------------------
# Capture
# -----------------------------------------------

def capture_frame():
    cap = cv2.VideoCapture(WEBCAM_INDEX)
    if not cap.isOpened():
        print("  [Webcam]: Could not open camera")
        return None

    try:
        for _ in range(3):
            cap.read()
        ret, frame = cap.read()
        return frame if ret else None
    finally:
        cap.release()

# -----------------------------------------------
# Preprocessing (IMPORTANT FOR OCR)
# -----------------------------------------------

def preprocess_for_ocr(image):
    # Resize
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.8, beta=20)

    # Gaussian blur (light)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # ✅ ADAPTIVE threshold (key fix)
    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)

    return thresh

# -----------------------------------------------
# OCR
# -----------------------------------------------

def extract_text(image):
    try:
        processed = preprocess_for_ocr(image)

        raw = pytesseract.image_to_string(
            processed,
            config=TESSERACT_CONFIG
        )

        clean = " ".join(raw.split())
        clean = re.sub(r'\s+', ' ', clean)

        return clean

    except Exception as e:
        print(f"  [OCR Error]: {e}")
        return ""

# -----------------------------------------------
# Save image
# -----------------------------------------------

def save_image(image, session_path, img_count):
    images_dir = os.path.join(session_path, "images")
    os.makedirs(images_dir, exist_ok=True)

    filepath = os.path.join(images_dir, f"img_{img_count:03d}.jpg")
    cv2.imwrite(filepath, image)

    return filepath

# -----------------------------------------------
# Main OCR Loop
# -----------------------------------------------

def run_ocr_loop(session_path, stop_event):
    from utils.session import append_to_notes

    img_count = 0
    last_text = ""

    print(f"  [OCR]: Loop started (every {CAPTURE_INTERVAL}s)")

    while not stop_event.is_set():
        image = capture_frame()

        if image is not None:
            img_count += 1
            save_image(image, session_path, img_count)

            # ✅ Save processed image (for debugging)
            processed = preprocess_for_ocr(image)
            cv2.imwrite(f"{session_path}/processed_{img_count}.jpg", processed)

            text = extract_text(image)

            if len(text.strip()) > 5 and text != last_text:
                append_to_notes(session_path, text)
                last_text = text
                print(f"  [OCR]: ✓ Saved {len(text)} chars (img {img_count})")
            else:
                if img_count % 5 == 0:
                    print("  [OCR]: scanning...")

        else:
            print("  [OCR]: Webcam capture failed — skipping")

        # Wait interval
        for _ in range(CAPTURE_INTERVAL):
            if stop_event.is_set():
                break
            time.sleep(1)

    print("  [OCR]: Loop stopped")