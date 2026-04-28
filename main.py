"""
AbleTab Laptop Prototype - main.py
====================================
Entry point. Runs in VS Code terminal.
Asks user to choose a mode via keyboard (no voice needed at start).

Hardware replaced:
  - Raspberry Pi      → Your laptop
  - ESP32-CAM         → Laptop webcam (cv2.VideoCapture)
  - Physical speaker  → Laptop speakers (pyttsx3)
  - USB Microphone    → Laptop built-in mic
"""

import os
import sys
import time
from sign_language.gesture_mapper import map_text_to_gesture
from sign_language.avatar_player import play_gesture



sys.path.insert(0, os.path.dirname(__file__))

from utils.tts import speak
from utils.session import create_session_folder

def run_sign_language(text):
    from sign_language.gesture_mapper import map_text_to_gesture
    from sign_language.avatar_player import play_gesture

    gestures = map_text_to_gesture(text)
    play_gesture(gestures)



def choose_mode():
    """
    Choose mode via keyboard input.
    Voice selection is optional (keyboard is more reliable for prototyping).
    """
    print("\n" + "=" * 45)
    print("  AbleTab - Inclusive Learning Tablet")
    print("         [ LAPTOP PROTOTYPE ]")
    print("=" * 45)
    print("\n  1 → Live Class Mode  (record + OCR)")
    print("  2 → Revision Mode    (voice navigation)")
    print()

    speak("Welcome to AbleTab. Press 1 for Live Class. Press 2 for Revision.")

    while True:
        choice = input("  Enter choice (1 or 2): ").strip()
        if choice == "1":
            return "live"
        elif choice == "2":
            return "revision"
        else:
            print("  Please enter 1 or 2.")


def main():
    mode = choose_mode()

    if mode == "live":
        speak("Starting Live Class Mode.")
        session_folder = create_session_folder()
        
        # 🔥 TEMP TEST (remove later)
        sample_text = "hello yes"
        print("\n[Sign Language Output - Live Mode]")
        run_sign_language(sample_text)

        from modes.live_class import run_live_class
        run_live_class(session_folder)

    elif mode == "revision":
        speak("Starting Revision Mode.")

        # 🔥 TEMP TEST (remove later)
        sample_text = "thanks no"
        print("\n[Sign Language Output - Revision Mode]")
        run_sign_language(sample_text)

        from modes.revision import run_revision
        run_revision()


if __name__ == "__main__":
    main()