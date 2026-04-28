"""
setup_dataset.py
----------------
Utility script to:
  1. Create required folder structure
  2. Generate a starter word_map.json
  3. Generate a sample ISL-CSLRT metadata.json (for testing)
  4. Verify your dataset is set up correctly
  5. Create dummy test videos (2-second colour clips) so you can
     run the full system before you have real sign videos.

Run once:  python setup_dataset.py
"""

import json
import os
import cv2
import numpy as np
from pathlib import Path


BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
WORD_DIR     = DATA_DIR / "word_signs"
ALPHA_DIR    = DATA_DIR / "fingerspelling"
CSLRT_DIR    = DATA_DIR / "isl_cslrt"


# ──────────────────────────────────────────────
# 1. CREATE FOLDER STRUCTURE
# ──────────────────────────────────────────────

def create_folders():
    for d in [WORD_DIR, ALPHA_DIR, CSLRT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}")


# ──────────────────────────────────────────────
# 2. STARTER word_map.json
# ──────────────────────────────────────────────

STARTER_WORDS = [
    # Core vocabulary for classroom / education demo
    "hello", "goodbye", "yes", "no", "please", "sorry",
    "thank_you", "help", "understand", "repeat",
    "school", "teacher", "student", "book", "learn",
    "what", "who", "where", "when", "why", "how",
    "name", "you", "i", "we", "they",
    "good", "bad", "big", "small",
    "today", "tomorrow", "now",
    "go", "come", "sit", "stand", "write", "read",
    "eat", "drink", "sleep",
    "mother", "father", "friend",
    "not", "more", "same", "different",
]

def create_word_map():
    """
    Creates word_map.json.
    Initially maps each word to the expected video path.
    Replace with real paths once you have sign videos.
    """
    mapping = {}
    for word in STARTER_WORDS:
        video_name = f"{word}.mp4"
        mapping[word] = f"word_signs/{video_name}"

    out_path = DATA_DIR / "word_map.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"  ✓ word_map.json  ({len(mapping)} entries)")


# ──────────────────────────────────────────────
# 3. SAMPLE ISL-CSLRT metadata.json
# ──────────────────────────────────────────────

SAMPLE_CSLRT_SENTENCES = {
    "sentence_001": "what is your name",
    "sentence_002": "i am going to school",
    "sentence_003": "please help me",
    "sentence_004": "i do not understand",
    "sentence_005": "can you repeat that",
    "sentence_006": "good morning teacher",
    "sentence_007": "i want to learn",
    "sentence_008": "where is the book",
    "sentence_009": "thank you very much",
    "sentence_010": "sit down please",
}

def create_cslrt_metadata():
    meta_path = CSLRT_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_CSLRT_SENTENCES, f, indent=2)
    print(f"  ✓ isl_cslrt/metadata.json  ({len(SAMPLE_CSLRT_SENTENCES)} entries)")


# ──────────────────────────────────────────────
# 4. DUMMY COLOUR VIDEOS (for testing without real clips)
# ──────────────────────────────────────────────

COLOURS = {
    "sign":        (0,  180,  80),   # green
    "alpha":       (180, 100, 0),    # orange
    "cslrt":       (20,  100, 200),  # blue
}

def _make_dummy_video(path: Path, label: str, colour: tuple,
                      fps: int = 25, duration_s: float = 1.5):
    """Creates a short coloured MP4 with the label as text."""
    if path.exists():
        return   # don't overwrite

    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (640, 480)
    )
    n_frames = int(fps * duration_s)
    for _ in range(n_frames):
        frame = np.full((480, 640, 3), colour, dtype=np.uint8)
        cv2.putText(frame, label.upper(), (40, 260),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.2,
                    (255, 255, 255), 3, cv2.LINE_AA)
        writer.write(frame)
    writer.release()


def create_dummy_videos():
    """
    Creates placeholder MP4 clips so the pipeline runs end-to-end
    without real sign language videos.

    DELETE / REPLACE these with real sign videos for production.
    """
    print("\n  Creating dummy sign videos (placeholders) …")

    # Word signs
    for word in STARTER_WORDS:
        _make_dummy_video(
            WORD_DIR / f"{word}.mp4",
            word, COLOURS["sign"]
        )

    # Alphabet (a-z)
    for c in "abcdefghijklmnopqrstuvwxyz":
        _make_dummy_video(
            ALPHA_DIR / f"{c}.mp4",
            c, COLOURS["alpha"]
        )

    # CSLRT sentence clips
    for clip_id in SAMPLE_CSLRT_SENTENCES:
        _make_dummy_video(
            CSLRT_DIR / f"{clip_id}.mp4",
            clip_id, COLOURS["cslrt"]
        )

    print("  ✓ Placeholder videos created.")
    print("  ⚠  Replace with real ISL sign videos before demo.")


# ──────────────────────────────────────────────
# 5. VERIFY SETUP
# ──────────────────────────────────────────────

def verify():
    print("\n── Verification ────────────────────────────")
    word_count  = len(list(WORD_DIR.glob("*.mp4")))
    alpha_count = len(list(ALPHA_DIR.glob("*.mp4")))
    cslrt_count = len(list(CSLRT_DIR.glob("*.mp4")))
    meta_ok = (CSLRT_DIR / "metadata.json").exists()

    print(f"  Word signs     : {word_count}")
    print(f"  Alphabet signs : {alpha_count}")
    print(f"  CSLRT clips    : {cslrt_count}")
    print(f"  CSLRT metadata : {'✓' if meta_ok else '✗ MISSING'}")

    if alpha_count < 26:
        missing = [c for c in "abcdefghijklmnopqrstuvwxyz"
                   if not (ALPHA_DIR / f"{c}.mp4").exists()]
        print(f"  ⚠  Missing alphabet letters: {', '.join(missing)}")
    else:
        print("  ✓ Full alphabet coverage")

    print("\n  System ready for demo! Run:  python main.py")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔧  ISL Avatar — Dataset Setup")
    print("=" * 45)

    print("\nCreating folder structure …")
    create_folders()

    print("\nGenerating config files …")
    create_word_map()
    create_cslrt_metadata()

    print("\nGenerating dummy placeholder videos …")
    create_dummy_videos()

    verify()
