"""
avatar_player.py
----------------
Plays gesture video clips using OpenCV.

Features:
  • Plays a single video file
  • Plays a sequence of GestureTokens with smooth transitions
  • Handles fingerspelling (plays one char at a time)
  • Pause frames between signs
  • Overlay: shows current word being signed
  • Non-blocking mode (runs in separate thread) for live pipeline
"""

import cv2
import time
import threading
import numpy as np
from pathlib import Path
from gesture_mapper import GestureToken


# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────

WINDOW_NAME   = "ISL Avatar"
PAUSE_FRAMES  = 8          # blank frames between signs (~0.25 s at 30 fps)
FS_PAUSE      = 6          # shorter pause between fingerspell chars
FONT          = cv2.FONT_HERSHEY_SIMPLEX
DISPLAY_W     = 640
DISPLAY_H     = 480
BG_COLOR      = (30, 30, 30)       # dark background for missing videos
TEXT_COLOR    = (255, 255, 255)
ACCENT_COLOR  = (0, 220, 150)      # teal highlight


# ──────────────────────────────────────────────
# LOW-LEVEL HELPERS
# ──────────────────────────────────────────────

def _blank_frame(label: str = "", sub: str = "") -> np.ndarray:
    """Creates a placeholder frame with optional text labels."""
    frame = np.full((DISPLAY_H, DISPLAY_W, 3), BG_COLOR, dtype=np.uint8)
    if label:
        cv2.putText(frame, label, (30, DISPLAY_H // 2 - 20),
                    FONT, 1.2, ACCENT_COLOR, 2, cv2.LINE_AA)
    if sub:
        cv2.putText(frame, sub, (30, DISPLAY_H // 2 + 30),
                    FONT, 0.6, TEXT_COLOR, 1, cv2.LINE_AA)
    return frame


def _overlay_label(frame: np.ndarray, word: str, mode: str = "") -> np.ndarray:
    """Draws word label at bottom of frame (non-destructive)."""
    out = frame.copy()
    bar_h = 40
    cv2.rectangle(out, (0, DISPLAY_H - bar_h), (DISPLAY_W, DISPLAY_H),
                  (0, 0, 0), -1)
    label = f"  {word.upper()}"
    if mode:
        label += f"  [{mode}]"
    cv2.putText(out, label, (10, DISPLAY_H - 12),
                FONT, 0.65, ACCENT_COLOR, 1, cv2.LINE_AA)
    return out


def _play_video_file(path: str, word_label: str = "",
                     mode: str = "", fps_override: int = 0) -> bool:
    """
    Plays a single video file in the ISL Avatar window.
    Returns True on success, False on failure.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"[Player] Cannot open: {path}")
        return False

    fps = fps_override or int(cap.get(cv2.CAP_PROP_FPS)) or 25
    delay = max(1, int(1000 / fps))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))
        frame = _overlay_label(frame, word_label, mode)
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(delay) & 0xFF in (ord('q'), 27):
            cap.release()
            return False        # signal: user quit

    cap.release()
    return True


def _show_pause(n_frames: int = PAUSE_FRAMES, label: str = "") -> bool:
    """Shows blank frames as a brief pause between signs."""
    frame = _blank_frame()
    if label:
        frame = _overlay_label(frame, label, "pause")
    delay = 33
    for _ in range(n_frames):
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(delay) & 0xFF in (ord('q'), 27):
            return False
    return True


# ──────────────────────────────────────────────
# MAIN PLAYER CLASS
# ──────────────────────────────────────────────

class AvatarPlayer:
    """
    Manages the OpenCV window and plays GestureToken sequences.
    Can run blocking (for simple scripts) or in a background thread.
    """

    def __init__(self, threaded: bool = False):
        self.threaded = threaded
        self._stop_event = threading.Event()
        self._queue: list = []
        self._lock = threading.Lock()
        self._thread = None

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, DISPLAY_W, DISPLAY_H)

        if threaded:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    # ── Public API ──────────────────────────────

    def play_tokens(self, tokens: list[GestureToken], block: bool = True):
        """
        Play a list of GestureTokens.
        block=True  → wait until done (use in non-threaded mode)
        block=False → add to queue (use in threaded mode)
        """
        if self.threaded and not block:
            with self._lock:
                self._queue.extend(tokens)
        else:
            self._render_tokens(tokens)

    def play_cslrt_video(self, path: str):
        """Play a raw ISL-CSLRT sentence-level video directly."""
        print(f"[Player] Playing CSLRT sentence clip: {path}")
        _play_video_file(path, "ISL-CSLRT", "sentence")

    def show_text_caption(self, text: str, duration_ms: int = 2000):
        """Shows a caption overlay (while signing is happening)."""
        frame = _blank_frame(text, "caption")
        cv2.imshow(WINDOW_NAME, frame)
        cv2.waitKey(duration_ms)

    def stop(self):
        self._stop_event.set()

    def close(self):
        self.stop()
        cv2.destroyWindow(WINDOW_NAME)

    # ── Internal rendering ───────────────────────

    def _render_tokens(self, tokens: list[GestureToken]):
        for token in tokens:
            if self._stop_event.is_set():
                break

            if token.token_type == "pause":
                if not _show_pause(PAUSE_FRAMES, token.word):
                    break

            elif token.token_type == "sign":
                ok = _play_video_file(
                    token.video_path,
                    word_label=token.word,
                    mode="sign"
                )
                if not ok:
                    # Video file missing — show placeholder
                    self._show_missing(token.word, "sign")

            elif token.token_type == "fingerspell":
                self._render_fingerspell(token)

    def _render_fingerspell(self, token: GestureToken):
        """Plays each character video in sequence for fingerspelling."""
        label_prefix = f"FS: {token.word.upper()} → "
        for i, (char, path) in enumerate(token.fingerspell_chars):
            if self._stop_event.is_set():
                break
            label = label_prefix + char.upper()
            ok = _play_video_file(path, word_label=label, mode="fingerspell")
            if not ok:
                self._show_missing(char, "fingerspell")
            # Very short pause between chars
            if i < len(token.fingerspell_chars) - 1:
                _show_pause(FS_PAUSE)

    def _show_missing(self, word: str, mode: str):
        """Placeholder for missing video files."""
        frame = _blank_frame(
            f"[{word.upper()}]",
            f"Video not found ({mode})"
        )
        cv2.imshow(WINDOW_NAME, frame)
        cv2.waitKey(600)

    def _worker(self):
        """Background thread: drains token queue continuously."""
        while not self._stop_event.is_set():
            with self._lock:
                if self._queue:
                    batch = self._queue[:]
                    self._queue.clear()
                else:
                    batch = []
            if batch:
                self._render_tokens(batch)
            else:
                time.sleep(0.05)


# ──────────────────────────────────────────────
# Quick self-test (plays a dummy video)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    from gesture_mapper import GestureToken
    player = AvatarPlayer()
    dummy_tokens = [
        GestureToken("hello",  None, "pause"),
        GestureToken("world",  None, "pause"),
    ]
    player.play_tokens(dummy_tokens)
    player.close()
