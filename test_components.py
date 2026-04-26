"""
test_components.py — AbleTab Laptop Component Tests
=====================================================
Run BEFORE main.py to verify all components work.
Each test prints PASS or FAIL with fix instructions.

Usage:
  python test_components.py
"""

import sys
import os
import platform

sys.path.insert(0, os.path.dirname(__file__))

GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
RESET = "\033[0m"
PASS  = f"{GREEN}✓ PASS{RESET}"
FAIL  = f"{RED}✗ FAIL{RESET}"
WARN  = f"{YELLOW}~ WARN{RESET}"


def section(title):
    print(f"\n  {'─'*45}")
    print(f"  {title}")
    print(f"  {'─'*45}")


# ──────────────────────────────────────────────────
# Test 1: TTS
# ──────────────────────────────────────────────────
def test_tts():
    section("1. Text-to-Speech (pyttsx3)")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say("AbleTab text to speech test.")
        engine.runAndWait()
        print(f"  {PASS}  pyttsx3 speaks correctly")
        return True
    except ImportError:
        print(f"  {FAIL}  pyttsx3 not installed")
        print(f"         Fix: pip install pyttsx3")
        return False
    except Exception as e:
        print(f"  {FAIL}  pyttsx3 error: {e}")
        if platform.system() == "Linux":
            print(f"         Fix: sudo apt install espeak")
        return False


# ──────────────────────────────────────────────────
# Test 2: Microphone
# ──────────────────────────────────────────────────
def test_microphone():
    section("2. Microphone (SpeechRecognition)")
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print(f"  {PASS}  Microphone accessible")
        print(f"  {PASS}  SpeechRecognition ready")

        # Quick 3-second listen test
        print(f"\n  Speak anything for 3 seconds to test recognition...")
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=4, phrase_time_limit=3)
        try:
            text = r.recognize_google(audio)
            print(f"  {PASS}  Google STT heard: '{text}'")
        except sr.UnknownValueError:
            print(f"  {WARN}  Mic works but couldn't understand speech")
        except sr.RequestError:
            print(f"  {WARN}  No internet — Google STT unavailable")
            print(f"         Keyboard fallback will be used instead")
        return True
    except ImportError:
        print(f"  {FAIL}  SpeechRecognition not installed")
        print(f"         Fix: pip install SpeechRecognition")
        return False
    except Exception as e:
        print(f"  {FAIL}  Microphone error: {e}")
        print(f"         Check: Is your laptop mic enabled in system settings?")
        return False


# ──────────────────────────────────────────────────
# Test 3: Webcam
# ──────────────────────────────────────────────────
def test_webcam():
    section("3. Webcam (OpenCV)")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print(f"  {FAIL}  Could not open webcam (index 0)")
            print(f"         Fix: Check webcam is connected and not used by another app")
            return False
        ret, frame = cap.read()
        cap.release()
        if ret:
            h, w = frame.shape[:2]
            print(f"  {PASS}  Webcam captures frames ({w}x{h})")
            # Save a test image
            os.makedirs("sessions", exist_ok=True)
            cv2.imwrite("sessions/webcam_test.jpg", frame)
            print(f"  {PASS}  Test image saved → sessions/webcam_test.jpg")
            return True
        else:
            print(f"  {FAIL}  Webcam opened but couldn't read frame")
            return False
    except ImportError:
        print(f"  {FAIL}  OpenCV not installed")
        print(f"         Fix: pip install opencv-python")
        return False


# ──────────────────────────────────────────────────
# Test 4: Tesseract OCR
# ──────────────────────────────────────────────────
def test_ocr():
    section("4. Tesseract OCR")
    try:
        import pytesseract
        import cv2
        import numpy as np

        # Create a simple test image with text
        img = np.ones((80, 360, 3), dtype=np.uint8) * 255
        cv2.putText(img, "AbleTab OCR Test", (15, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)

        text = pytesseract.image_to_string(img).strip()
        if text:
            print(f"  {PASS}  Tesseract OCR works")
            print(f"  {PASS}  OCR read: '{text}'")
        else:
            print(f"  {WARN}  Tesseract ran but returned no text")
            print(f"         (This may be normal for synthetic test images)")
        return True

    except pytesseract.TesseractNotFoundError:
        print(f"  {FAIL}  Tesseract binary not found")
        print(f"\n         Install Tesseract:")
        if platform.system() == "Windows":
            print(f"           https://github.com/UB-Mannheim/tesseract/wiki")
            print(f"           After install, add to PATH:")
            print(f"           C:\\Program Files\\Tesseract-OCR")
        elif platform.system() == "Darwin":
            print(f"           brew install tesseract")
        else:
            print(f"           sudo apt install tesseract-ocr")
        return False
    except ImportError:
        print(f"  {FAIL}  pytesseract not installed")
        print(f"         Fix: pip install pytesseract")
        return False


# ──────────────────────────────────────────────────
# Test 5: Audio Recording
# ──────────────────────────────────────────────────
def test_audio_recording():
    section("5. Audio Recording (sounddevice / pyaudio)")
    try:
        import sounddevice as sd
        import numpy as np
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        print(f"  {PASS}  sounddevice works ({len(input_devices)} input device(s) found)")

        # 2-second test recording
        print(f"         Recording 2 seconds of test audio...")
        audio = sd.rec(2 * 16000, samplerate=16000, channels=1, dtype='int16', blocking=True)
        print(f"  {PASS}  2-second recording captured ({len(audio)} samples)")
        return True
    except ImportError:
        pass

    # Fallback: pyaudio
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        count = p.get_device_count()
        p.terminate()
        print(f"  {PASS}  pyaudio works ({count} device(s) found)")
        return True
    except ImportError:
        print(f"  {FAIL}  Neither sounddevice nor pyaudio installed")
        print(f"         Fix: pip install sounddevice scipy")
        return False
    except Exception as e:
        print(f"  {FAIL}  Audio recording error: {e}")
        return False


# ──────────────────────────────────────────────────
# Test 6: Audio Playback
# ──────────────────────────────────────────────────
def test_audio_playback():
    section("6. Audio Playback")
    system = platform.system()
    print(f"  Platform: {system}")

    if system == "Windows":
        try:
            import winsound
            print(f"  {PASS}  winsound available (Windows built-in)")
            return True
        except Exception:
            pass

    elif system == "Darwin":
        import subprocess
        result = subprocess.run(["which", "afplay"], capture_output=True)
        if result.returncode == 0:
            print(f"  {PASS}  afplay available (macOS built-in)")
            return True

    else:  # Linux
        import subprocess
        result = subprocess.run(["which", "aplay"], capture_output=True)
        if result.returncode == 0:
            print(f"  {PASS}  aplay available (Linux built-in)")
            return True
        else:
            print(f"  {FAIL}  aplay not found")
            print(f"         Fix: sudo apt install alsa-utils")
            return False

    print(f"  {WARN}  No built-in player found — install pygame as fallback")
    print(f"         Fix: pip install pygame")
    return False


# ──────────────────────────────────────────────────
# Test 7: Session Manager
# ──────────────────────────────────────────────────
def test_session():
    section("7. Session Manager")
    try:
        from utils.session import create_session_folder, append_to_notes, get_notes_text
        session = create_session_folder()
        append_to_notes(session, "Component test entry.")
        text = get_notes_text(session)
        assert "Component test" in text
        print(f"  {PASS}  Session folder created")
        print(f"  {PASS}  Notes read/write works")
        print(f"         Path: {session}")
        return True
    except Exception as e:
        print(f"  {FAIL}  Session manager error: {e}")
        return False


# ──────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────
def run_all():
    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║    AbleTab — Component Test Suite       ║")
    print(f"  ║    Platform: {platform.system():<29}║")
    print("  ╚══════════════════════════════════════════╝")

    tests = [
        ("TTS",              test_tts),
        ("Microphone",       test_microphone),
        ("Webcam",           test_webcam),
        ("OCR",              test_ocr),
        ("Audio Recording",  test_audio_recording),
        ("Audio Playback",   test_audio_playback),
        ("Session Manager",  test_session),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = False
            print(f"  {FAIL}  Unexpected error in {name}: {e}")

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n  {'─'*45}")
    print(f"  SUMMARY: {passed}/{total} tests passed")
    print(f"  {'─'*45}")
    for name, ok in results.items():
        icon = PASS if ok else FAIL
        print(f"    {icon}  {name}")

    print()
    if passed == total:
        print(f"  {GREEN}All systems ready! Run: python main.py{RESET}\n")
    else:
        failed = [n for n, v in results.items() if not v]
        print(f"  {RED}Fix these before running:{RESET} {', '.join(failed)}\n")


if __name__ == "__main__":
    run_all()
