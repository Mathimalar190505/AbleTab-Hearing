"""
modes/live_class.py - Live Class Mode (Laptop Version)
=========================================================
Runs three things in parallel using threads:
  1. Audio recording   → mic → WAV chunks (10 min each)
  2. OCR pipeline      → webcam → Tesseract → notes.txt
  3. Stop listener     → waits for ENTER key or "exit" voice command

All activity is printed to the VS Code terminal for visibility.
"""

import threading
import time
import os
import sys

from utils.tts import speak
from utils.audio_recorder import AudioRecorder
from utils.ocr_pipeline import run_ocr_loop
from utils.session import get_notes_text, get_audio_files


def run_live_class(session_path):
    """
    Main Live Class Mode function.
    Starts recording and OCR, waits for user to stop session.
    """
    _print_banner(session_path)

    speak("Live class mode started. Recording audio and capturing notes.")
    speak("Press Enter in terminal to stop recording.")

    stop_event = threading.Event()

    # --- Thread 1: Audio Recorder ---
    recorder = AudioRecorder(session_path)
    recorder.start()

    # --- Thread 2: OCR Pipeline ---
    ocr_thread = threading.Thread(
        target=run_ocr_loop,
        args=(session_path, stop_event),
        daemon=True
    )
    ocr_thread.start()

    # --- Thread 3: Status display ---
    status_thread = threading.Thread(
        target=_status_loop,
        args=(session_path, stop_event, recorder),
        daemon=True
    )
    status_thread.start()

    # --- Main thread: Wait for ENTER to stop ---
    try:
        print("\n  ┌─────────────────────────────────────────┐")
        print("  │  Recording in progress...                │")
        print("  │  Press  ENTER  to stop the session       │")
        print("  └─────────────────────────────────────────┘\n")
        input()  # Block until ENTER
    except KeyboardInterrupt:
        print("\n  [Ctrl+C detected]")

    # --- Stop all threads ---
    print("\n  [Stopping session...]")
    stop_event.set()
    recorder.stop()
    ocr_thread.join(timeout=5)
    status_thread.join(timeout=3)

    # --- Print + speak session summary ---
    _print_summary(session_path, recorder)


def _status_loop(session_path, stop_event, recorder):
    """
    Prints live status every 30 seconds to terminal.
    Gives voice update every 5 minutes.
    """
    start_time = time.time()
    last_voice_min = 0

    while not stop_event.is_set():
        time.sleep(30)
        if stop_event.is_set():
            break

        elapsed_sec = int(time.time() - start_time)
        elapsed_min = elapsed_sec // 60
        chunks = recorder.get_chunk_count()

        print(f"\n  [Status] {elapsed_min}m {elapsed_sec % 60}s elapsed"
              f" | {chunks} audio chunk(s) saved")

        # Voice update every 5 minutes
        if elapsed_min > 0 and elapsed_min % 5 == 0 and elapsed_min != last_voice_min:
            last_voice_min = elapsed_min
            speak(f"{elapsed_min} minutes recorded.")


def _print_summary(session_path, recorder):
    """Print and speak a summary of the captured session."""
    audio_files = get_audio_files(session_path)
    notes = get_notes_text(session_path)
    word_count = len(notes.split()) if notes else 0

    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║          SESSION SUMMARY                 ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  Audio chunks : {len(audio_files):<25}║")
    print(f"  ║  Notes words  : {word_count:<25}║")
    print(f"  ║  Session path : sessions/ folder        ║")
    print("  ╚══════════════════════════════════════════╝\n")

    speak(f"Session complete. {len(audio_files)} audio files saved.")
    speak(f"Notes contain {word_count} words.")
    speak("Switch to revision mode to review.")


def _print_banner(session_path):
    """Print a clear header to the terminal."""
    folder_name = os.path.basename(session_path)
    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║       AbleTab — LIVE CLASS MODE          ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  Session: {folder_name[:33]:<33}║")
    print("  ╠══════════════════════════════════════════╣")
    print("  ║  🎤 Recording mic audio (10 min chunks)  ║")
    print("  ║  📷 Capturing webcam → OCR every 12s     ║")
    print("  ║  📝 Saving text to notes.txt              ║")
    print("  ╚══════════════════════════════════════════╝")
