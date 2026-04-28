"""
main.py
-------
Your EXISTING main.py, extended with ISL Avatar support.

Original flow  (already working):
  Microphone → SpeechRecognition → text caption → display

New flow:
  Microphone → SpeechRecognition → text caption → display
                                              ↘ ISL Sign Avatar

HOW TO INTEGRATE:
  1. Add the three import lines marked NEW
  2. Add pipeline = SignPipeline() after your existing setup
  3. After you get a caption string, call:
       pipeline.process_caption(caption_text)

Everything below is a COMPLETE working example.
Replace the ... sections with your own existing code.
"""

import speech_recognition as sr
import threading
import time

# ── NEW: import sign pipeline ──────────────────
from sign_pipeline import SignPipeline
# ──────────────────────────────────────────────


# ══════════════════════════════════════════════
# YOUR EXISTING CAPTION DISPLAY FUNCTION
# (replace this with however you show captions)
# ══════════════════════════════════════════════
def display_caption(text: str):
    """Stub — replace with your actual caption display logic."""
    print(f"\n📝 CAPTION: {text}")


# ══════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════

def main():
    print("=" * 55)
    print("  ISL Avatar System — Hearing Impaired Assistant")
    print("=" * 55)

    # ── NEW: initialise ISL pipeline once ─────
    pipeline = SignPipeline(
        threaded_player=False,   # True = avatar runs in background thread
        use_isl_grammar=True,    # Apply SOV conversion
        prefer_cslrt=True        # Try sentence-level match first
    )
    # ──────────────────────────────────────────

    # ── YOUR EXISTING: speech recogniser setup ─
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("\nListening … (Ctrl-C to quit)\n")

    try:
        while True:
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    print("🎤 Speak now …", end=" ", flush=True)
                    audio = recognizer.listen(
                        source, timeout=5, phrase_time_limit=10
                    )

                # ── YOUR EXISTING: speech-to-text ──────
                caption_text = recognizer.recognize_google(
                    audio, language="en-IN"
                )
                print(f"✓ \"{caption_text}\"")

                # ── YOUR EXISTING: show caption ─────────
                display_caption(caption_text)

                # ── NEW: sign it! ───────────────────────
                pipeline.process_caption(caption_text)
                # ────────────────────────────────────────

            except sr.WaitTimeoutError:
                print("(silence)")
            except sr.UnknownValueError:
                print("(not understood)")
            except sr.RequestError as e:
                print(f"(STT error: {e})")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nShutting down …")
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
