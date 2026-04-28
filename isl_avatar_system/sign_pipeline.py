"""
sign_pipeline.py
----------------
Orchestrates the full pipeline:
  Audio/Text Input
      ↓
  ISL-CSLRT sentence-level check (try realistic match first)
      ↓  (no match)
  ISL Grammar Conversion  (SOV, drop articles, etc.)
      ↓
  Word → Sign Video Mapping
      ↓
  Fallback: Fingerspelling for unknown words
      ↓
  OpenCV Avatar Playback  (with captions)

Usage:
  pipeline = SignPipeline()
  pipeline.run_from_text("What is your name?")
  pipeline.run_from_audio()  # uses SpeechRecognition
"""

import time
import threading
from isl_preprocessor import ISLPreprocessor
from gesture_mapper     import GestureMapper
from avatar_player      import AvatarPlayer


class SignPipeline:
    """
    Top-level coordinator.  Initialize once, call run_from_text()
    or run_from_audio() repeatedly.
    """

    def __init__(self, threaded_player: bool = False,
                 use_isl_grammar: bool = True,
                 prefer_cslrt: bool = True):
        """
        threaded_player : run avatar in background thread (use for real-time)
        use_isl_grammar : apply SOV reorder & word drops
        prefer_cslrt    : try sentence-level ISL-CSLRT match first
        """
        self.use_isl_grammar = use_isl_grammar
        self.prefer_cslrt    = prefer_cslrt

        print("[Pipeline] Initialising ISL system …")
        self.preprocessor = ISLPreprocessor()
        self.mapper        = GestureMapper(self.preprocessor)
        self.player        = AvatarPlayer(threaded=threaded_player)
        print("[Pipeline] Ready.")

    # ──────────────────────────────────────────
    # PUBLIC: TEXT INPUT
    # ──────────────────────────────────────────

    def run_from_text(self, text: str):
        """
        Full pipeline from a text string.
        Prints coverage report, then plays signs.
        """
        if not text or not text.strip():
            return

        print(f"\n[Pipeline] Input: \"{text}\"")

        # Show caption overlay
        self.player.show_text_caption(text, duration_ms=1500)

        # --- Try sentence-level CSLRT first ---
        if self.prefer_cslrt:
            result = self.mapper.map_with_cslrt(text)
            if isinstance(result, str):
                # Got a CSLRT video path — play as single realistic clip
                self.player.play_cslrt_video(result)
                return

        # --- Word-level mapping ---
        tokens = self.mapper.map_sentence(
            text, use_isl_grammar=self.use_isl_grammar
        )

        # Print what will be played
        self._print_token_plan(tokens)

        # Play
        self.player.play_tokens(tokens, block=True)

    # ──────────────────────────────────────────
    # PUBLIC: AUDIO INPUT
    # ──────────────────────────────────────────

    def run_from_audio(self, language: str = "en-IN",
                       timeout: int = 5,
                       phrase_limit: int = 10):
        """
        Listens for one spoken sentence, converts to text,
        then calls run_from_text().
        Requires: pip install SpeechRecognition pyaudio
        """
        try:
            import speech_recognition as sr
        except ImportError:
            print("[Pipeline] SpeechRecognition not installed. "
                  "Run: pip install SpeechRecognition pyaudio")
            return None

        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        print("[Pipeline] Listening …")
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            text = recognizer.recognize_google(audio, language=language)
            print(f"[Pipeline] Recognised: \"{text}\"")
            self.run_from_text(text)
            return text
        except sr.WaitTimeoutError:
            print("[Pipeline] No speech detected.")
        except sr.UnknownValueError:
            print("[Pipeline] Speech not understood.")
        except sr.RequestError as e:
            print(f"[Pipeline] STT service error: {e}")
        return None

    # ──────────────────────────────────────────
    # PUBLIC: CONTINUOUS LOOP (for live demo)
    # ──────────────────────────────────────────

    def run_live_loop(self, language: str = "en-IN"):
        """
        Continuous listen → sign loop.
        Press Ctrl+C to stop.
        """
        print("[Pipeline] Live loop started.  Ctrl-C to quit.\n")
        try:
            while True:
                self.run_from_audio(language=language)
                time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n[Pipeline] Stopped.")
        finally:
            self.player.close()

    # ──────────────────────────────────────────
    # INTEGRATION HOOK for existing main.py
    # ──────────────────────────────────────────

    def process_caption(self, caption_text: str):
        """
        Drop-in method for existing captioning systems.
        Call this wherever your current system emits a caption string.

        Example in your main.py:
            pipeline.process_caption(caption)
        """
        self.run_from_text(caption_text)

    # ──────────────────────────────────────────
    # INTERNALS
    # ──────────────────────────────────────────

    def _print_token_plan(self, tokens):
        print("[Pipeline] Sign plan:")
        for t in tokens:
            if t.token_type == "pause":
                continue
            if t.token_type == "sign":
                print(f"   ✓  {t.word:15s}  [sign]  → {t.video_path}")
            elif t.token_type == "fingerspell":
                chars = "".join(c for c, _ in t.fingerspell_chars)
                print(f"   ~  {t.word:15s}  [fingerspell] → {chars}")
            else:
                print(f"   ✗  {t.word:15s}  [MISSING]")

    def close(self):
        self.player.close()


# ──────────────────────────────────────────────
# STANDALONE TEST
# ──────────────────────────────────────────────
if __name__ == "__main__":
    pipeline = SignPipeline()

    test_sentences = [
        "Hello, what is your name?",
        "I am going to school",
        "Yes, I understand",
    ]

    for sentence in test_sentences:
        pipeline.run_from_text(sentence)
        time.sleep(0.5)

    pipeline.close()
