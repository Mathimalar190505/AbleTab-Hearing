"""
utils/tts.py - Text-to-Speech (Laptop Version)
================================================
Uses pyttsx3 — works offline on Windows, macOS, Linux.

Windows  → uses SAPI5 (built-in)
macOS    → uses NSSpeechSynthesizer (built-in)
Linux    → uses espeak (install: sudo apt install espeak)

No internet required.
"""

import pyttsx3
import time
import sys

_engine = None


def _get_engine():
    """Initialize TTS engine once and reuse."""
    global _engine
    if _engine is None:
        try:
            _engine = pyttsx3.init()
            _engine.setProperty('rate', 155)      # Slightly slow for clarity
            _engine.setProperty('volume', 1.0)

            # On Windows/macOS: pick a clear voice if available
            voices = _engine.getProperty('voices')
            if voices:
                # Prefer female voice index 1 if available (often clearer)
                if len(voices) > 1:
                    _engine.setProperty('voice', voices[1].id)
                else:
                    _engine.setProperty('voice', voices[0].id)
        except Exception as e:
            print(f"[TTS Init Error]: {e}")
            print("  → On Linux: sudo apt install espeak")
            print("  → On macOS: should work out of the box")
            print("  → On Windows: should work out of the box")
    return _engine


def speak(text, pause_after=0.3):
    """
    Speak text aloud. Also prints to terminal for visual reference.
    
    Args:
        text (str): Message to speak
        pause_after (float): Pause in seconds after speaking
    """
    print(f"  🔊 {text}")
    try:
        engine = _get_engine()
        if engine:
            engine.say(text)
            engine.runAndWait()
        time.sleep(pause_after)
    except Exception as e:
        print(f"  [TTS Error]: {e}")
        global _engine
        _engine = None  # Reset so next call re-initializes


def speak_slow(text):
    """
    Speak at a slower rate — used when reading notes to blind users.
    """
    print(f"  🔊 [slow] {text}")
    try:
        engine = _get_engine()
        if engine:
            original_rate = engine.getProperty('rate')
            engine.setProperty('rate', 120)
            engine.say(text)
            engine.runAndWait()
            engine.setProperty('rate', original_rate)
    except Exception as e:
        print(f"  [TTS Error]: {e}")
