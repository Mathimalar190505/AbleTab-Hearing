"""
main_patch.py  ──  INTEGRATION GUIDE FOR YOUR EXISTING main.py
================================================================

This file shows you EXACTLY what lines to add/change in your existing
main.py. Search for the markers and insert the code blocks.

Your existing pipeline (unchanged):
  Audio → SpeechRecognition → text → display caption

What we add:
  text  ──→  SignLanguagePipeline.process_text(text)
                    ↓
             ISL preprocessing + gesture mapping
                    ↓
             AvatarPlayer (runs in background thread)

──────────────────────────────────────────────────────────────────
STEP 1  Add this import block at the TOP of your existing main.py
──────────────────────────────────────────────────────────────────
"""

# ── PASTE THIS AT THE TOP OF main.py ────────────────────────────
import sys
import os

# Make sign_language package importable regardless of working directory
_SIGN_MODULE_DIR = os.path.join(os.path.dirname(__file__), "sign_language")
if _SIGN_MODULE_DIR not in sys.path:
    sys.path.insert(0, _SIGN_MODULE_DIR)

from sign_language.sign_pipeline import SignLanguagePipeline

# ── GLOBAL PIPELINE OBJECT (place near your other globals) ───────
_sign_pipeline: SignLanguagePipeline = None


# ──────────────────────────────────────────────────────────────────
# STEP 2  Add this function near your app initialisation code
# ──────────────────────────────────────────────────────────────────

def init_sign_pipeline(
        assets_root: str = "sign_language/assets/gestures",
        playback_speed: float = 1.0,
        window_w: int = 640,
        window_h: int = 480,
        transition_ms: int = 200,
        headless: bool = False,
) -> SignLanguagePipeline:
    """
    Call once when your application starts (e.g., inside App.__init__
    or at module level before your main loop).
    """
    global _sign_pipeline
    _sign_pipeline = SignLanguagePipeline(
        assets_root=assets_root,
        window_w=window_w,
        window_h=window_h,
        transition_ms=transition_ms,
        playback_speed=playback_speed,
        headless=headless,
    )
    _sign_pipeline.start()
    print("[AbleTab] Sign Language Avatar started.")
    return _sign_pipeline


def shutdown_sign_pipeline():
    """Call in your app's on_close / cleanup code."""
    global _sign_pipeline
    if _sign_pipeline:
        _sign_pipeline.stop()
        _sign_pipeline = None


# ──────────────────────────────────────────────────────────────────
# STEP 3  Find your STT callback / wherever you get transcribed text
#         and add ONE line.
#
# Example: if your existing code looks like this:
#
#   def on_speech_result(self, text):
#       self.caption_label.config(text=text)   # ← already exists
#
# Change it to:
#
#   def on_speech_result(self, text):
#       self.caption_label.config(text=text)   # ← keep as-is
#       _sign_pipeline.process_text(text)      # ← ADD THIS LINE
#
# That's it. The pipeline is async so it won't block your UI thread.
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# STEP 4  Tkinter / GUI integration (if you use Tkinter)
#         Add to your existing window setup:
# ──────────────────────────────────────────────────────────────────

def integrate_with_tkinter(root_window):
    """
    If you use a Tkinter root window, call this after creating it.
    Adds sign language toggle button and graceful shutdown.
    """
    import tkinter as tk

    # Toggle button
    toggle_var = tk.BooleanVar(value=True)

    def toggle_sign():
        if toggle_var.get():
            _sign_pipeline.resume()
        else:
            _sign_pipeline.pause()

    btn = tk.Checkbutton(root_window, text="🤟 Sign Avatar",
                         variable=toggle_var, command=toggle_sign,
                         font=("Arial", 12), fg="white", bg="#222",
                         selectcolor="#444", activebackground="#333")
    btn.pack(side="bottom", pady=4)

    # Graceful shutdown on window close
    original_destroy = root_window.destroy

    def on_close():
        shutdown_sign_pipeline()
        original_destroy()

    root_window.protocol("WM_DELETE_WINDOW", on_close)


# ──────────────────────────────────────────────────────────────────
# STEP 5  OCR integration
#         If your OCR mode also produces text, hook it the same way:
#
#   def on_ocr_result(self, text):
#       self.ocr_label.config(text=text)    # ← already exists
#       _sign_pipeline.process_text(text)   # ← ADD THIS LINE
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# COMPLETE minimal main.py example (standalone, no existing code)
# ──────────────────────────────────────────────────────────────────

def _demo_standalone():
    """
    Minimal demo that mimics a speech-to-text → avatar pipeline.
    Run: python main_patch.py
    """
    import time

    pipeline = init_sign_pipeline(
        assets_root="sign_language/assets/gestures",
        headless=False,
    )

    test_sentences = [
        "Hello everyone, welcome to the class.",
        "Please open your books to page ten.",
        "The teacher will explain the lesson now.",
        "Do you understand the question?",
        "Write your answer on the board.",
        "The exam is tomorrow.",
        "I don't know the answer.",
        "Can you help me please?",
    ]

    print("\nStarting demo. Press Ctrl+C to stop.\n")
    try:
        for sentence in test_sentences:
            print(f"STT: {sentence}")
            result = pipeline.process_text(sentence)
            if result:
                print(f"ISL: {result['isl']}")
                print(f"     Coverage: {result['coverage']['coverage_pct']}%\n")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_sign_pipeline()
        print("Done.")


if __name__ == "__main__":
    _demo_standalone()
