"""
utils/voice_input.py - Voice Command Recognition (Laptop Version)
==================================================================
Uses laptop built-in microphone via SpeechRecognition library.

Two recognition modes:
  1. Google Web Speech (online) - more accurate
  2. Keyboard fallback         - type commands if mic fails

Only 5 commands are valid:
  "read notes"  "play audio"  "next"  "repeat"  "exit"

IMPORTANT: Google recognition needs internet.
For offline, install pocketsphinx:
  pip install pocketsphinx
"""

import speech_recognition as sr
import sys
import threading

_recognizer = sr.Recognizer()
_recognizer.energy_threshold = 400       # Adjust up if too much background noise
_recognizer.pause_threshold = 0.7
_recognizer.dynamic_energy_threshold = True  # Auto-adjust for laptop mic


def listen_once(timeout=6, phrase_limit=5):
    """
    Listen for one voice command from the laptop microphone.
    Falls back to keyboard input if mic fails or no speech detected.

    Returns matched command string or None.
    """
    print("\n  🎤 Listening... (or type a command below)")
    print("     Commands: read notes | play audio | next | repeat | exit")

    # Run mic and keyboard listener in parallel — whichever comes first wins
    result = [None]
    done = threading.Event()

    def mic_listener():
        try:
            with sr.Microphone() as source:
                _recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = _recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
            text = _recognizer.recognize_google(audio).lower()
            print(f"  [Heard]: '{text}'")
            matched = _match_command(text)
            if matched and not done.is_set():
                result[0] = matched
                done.set()
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            # No internet — try offline
            _try_offline(audio, result, done)
        except Exception as e:
            print(f"  [Mic Error]: {e}")
        finally:
            if not done.is_set():
                done.set()

    def keyboard_listener():
        try:
            text = input("  > ").strip().lower()
            matched = _match_command(text)
            if matched and not done.is_set():
                result[0] = matched
                done.set()
            elif not done.is_set():
                done.set()
        except EOFError:
            done.set()

    # Start both threads
    t1 = threading.Thread(target=mic_listener, daemon=True)
    t2 = threading.Thread(target=keyboard_listener, daemon=True)
    t1.start()
    t2.start()

    # Wait for either thread to produce a result
    done.wait(timeout=timeout + 3)

    if result[0] is None:
        print("  [No command detected]")

    return result[0]


def _try_offline(audio, result, done):
    """Try pocketsphinx offline recognition as fallback."""
    try:
        text = _recognizer.recognize_sphinx(audio).lower()
        print(f"  [Sphinx heard]: '{text}'")
        matched = _match_command(text)
        if matched and not done.is_set():
            result[0] = matched
    except Exception:
        pass  # Sphinx not installed or failed — keyboard fallback handles it


def _match_command(text):
    """
    Match spoken/typed text to one of 5 commands.
    Flexible keyword matching handles partial phrases.
    """
    if not text:
        return None

    text = text.strip().lower()

    if "read" in text or "note" in text:
        return "read notes"
    elif "play" in text or "audio" in text or "listen" in text:
        return "play audio"
    elif "next" in text or "skip" in text or text == "n":
        return "next"
    elif "repeat" in text or "again" in text or text == "r":
        return "repeat"
    elif "exit" in text or "quit" in text or "stop" in text or text == "q":
        return "exit"

    print(f"  [Unknown command]: '{text}'")
    print("  Valid: read notes | play audio | next | repeat | exit")
    return None
