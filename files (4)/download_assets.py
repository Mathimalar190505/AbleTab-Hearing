"""
download_assets.py
-------------------
Downloads / sets up ISL gesture assets for the avatar player.

Supported sources
-----------------
1. INCLUDE (Indian Sign Language dataset) – YouTube based, no direct API
2. ISL-CSLRT dataset (IITD) – manual download required; script validates
3. Synthetic fallback: generates solid-colour placeholder .mp4 files using
   OpenCV so the system works end-to-end before real videos are ready.

Run this once before starting the main pipeline:
    python download_assets.py --mode placeholder
    python download_assets.py --mode validate --root assets/gestures
"""

import os
import sys
import argparse
import logging
import subprocess

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Folder structure to create
# ---------------------------------------------------------------------------
REQUIRED_DIRS = [
    "assets/gestures/words",
    "assets/gestures/letters",
    "assets/gestures/special",
]

# Words for which we auto-generate placeholder videos
CORE_WORDS = [
    "HELLO", "BYE", "PLEASE", "THANK", "SORRY",
    "YES", "NO", "NOT", "CANNOT",
    "I", "YOU", "HE", "SHE", "WE", "THEY", "IT",
    "GO", "COME", "HELP", "KNOW", "WANT", "NEED",
    "EAT", "DRINK", "LEARN", "STUDY", "WRITE", "READ",
    "UNDERSTAND", "EXPLAIN", "TEACH", "LISTEN", "SEE",
    "THINK", "FEEL", "LIKE", "LOVE",
    "GOOD", "BAD", "BIG", "SMALL",
    "TEACHER", "STUDENT", "SCHOOL", "CLASS",
    "BOOK", "EXAM", "LESSON", "QUESTION", "ANSWER", "TEST",
    "TODAY", "TOMORROW", "YESTERDAY", "NOW", "FUTURE",
    "WHAT", "WHERE", "WHEN", "WHO", "HOW", "WHY",
]

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

COLORS_BY_CATEGORY = {
    "greeting":   (60, 180, 60),
    "pronoun":    (60, 130, 200),
    "verb":       (200, 130, 60),
    "adjective":  (180, 60, 180),
    "noun":       (60, 180, 180),
    "time":       (200, 180, 40),
    "question":   (200, 60, 60),
    "default":    (100, 100, 100),
    "letter":     (80, 80, 160),
    "special":    (40, 40, 40),
}

WORD_CATEGORY = {
    **{w: "greeting"  for w in ["HELLO","BYE","PLEASE","THANK","SORRY"]},
    **{w: "pronoun"   for w in ["I","YOU","HE","SHE","WE","THEY","IT"]},
    **{w: "verb"      for w in ["GO","COME","HELP","KNOW","WANT","NEED",
                                "EAT","DRINK","LEARN","STUDY","WRITE","READ",
                                "UNDERSTAND","EXPLAIN","TEACH","LISTEN","SEE",
                                "THINK","FEEL","LIKE","LOVE"]},
    **{w: "adjective" for w in ["GOOD","BAD","BIG","SMALL"]},
    **{w: "noun"      for w in ["TEACHER","STUDENT","SCHOOL","CLASS",
                                "BOOK","EXAM","LESSON","QUESTION","ANSWER","TEST"]},
    **{w: "time"      for w in ["TODAY","TOMORROW","YESTERDAY","NOW","FUTURE"]},
    **{w: "question"  for w in ["WHAT","WHERE","WHEN","WHO","HOW","WHY"]},
}


def _make_placeholder_video(path: str, label: str,
                             color: tuple, fps: int = 15, seconds: float = 1.2):
    """Write a solid-colour .mp4 with the word as text overlay."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (400, 300))
    frames = int(fps * seconds)
    for i in range(frames):
        frame = np.full((300, 400, 3), color, dtype=np.uint8)
        # Animate: slight brightness pulse
        pulse = int(20 * np.sin(2 * np.pi * i / frames))
        frame = np.clip(frame.astype(int) + pulse, 0, 255).astype(np.uint8)
        # Word text
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 1.2, 2)
        x, y = (400 - tw) // 2, (300 + th) // 2
        cv2.putText(frame, label, (x, y),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
        # Thin border
        cv2.rectangle(frame, (8, 8), (392, 292), (200, 200, 200), 2)
        out.write(frame)
    out.release()


def create_dirs():
    for d in REQUIRED_DIRS:
        os.makedirs(d, exist_ok=True)
        log.info("Created  %s", d)


def generate_placeholders(overwrite: bool = False):
    create_dirs()
    total = 0

    for word in CORE_WORDS:
        path = f"assets/gestures/words/{word}.mp4"
        if os.path.isfile(path) and not overwrite:
            continue
        cat = WORD_CATEGORY.get(word, "default")
        color = COLORS_BY_CATEGORY[cat]
        _make_placeholder_video(path, word, color)
        total += 1

    for letter in LETTERS:
        path = f"assets/gestures/letters/{letter}.mp4"
        if os.path.isfile(path) and not overwrite:
            continue
        _make_placeholder_video(path, letter, COLORS_BY_CATEGORY["letter"],
                                fps=12, seconds=0.5)
        total += 1

    for name in ["UNKNOWN", "PAUSE"]:
        path = f"assets/gestures/special/{name}.mp4"
        if os.path.isfile(path) and not overwrite:
            continue
        _make_placeholder_video(path, name, COLORS_BY_CATEGORY["special"],
                                fps=15, seconds=0.8)
        total += 1

    log.info("Generated %d placeholder videos.", total)
    return total


def validate(root: str = "assets/gestures"):
    """Check which words have real/placeholder videos."""
    words_dir = os.path.join(root, "words")
    letters_dir = os.path.join(root, "letters")
    missing_words = []
    missing_letters = []

    for w in CORE_WORDS:
        if not os.path.isfile(os.path.join(words_dir, f"{w}.mp4")):
            missing_words.append(w)

    for l in LETTERS:
        if not os.path.isfile(os.path.join(letters_dir, f"{l}.mp4")):
            missing_letters.append(l)

    total = len(CORE_WORDS) + len(LETTERS)
    found = total - len(missing_words) - len(missing_letters)
    print(f"\nCoverage: {found}/{total} ({100*found//total}%)")
    if missing_words:
        print(f"Missing words ({len(missing_words)}): {', '.join(missing_words)}")
    if missing_letters:
        print(f"Missing letters ({len(missing_letters)}): {', '.join(missing_letters)}")
    return len(missing_words) == 0 and len(missing_letters) == 0


def print_dataset_info():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           REAL ISL VIDEO DATASET SOURCES                         ║
╠══════════════════════════════════════════════════════════════════╣
║ 1. ISL-CSLRT (IIT Delhi)                                         ║
║    URL : https://www.iitd.ac.in/~pkalra/isl-cslrt/              ║
║    Type: Continuous ISL sentences, RGB + depth                   ║
║    Size: ~7000 videos, 200+ words                                ║
║    Use : Best for classroom vocab                                 ║
║                                                                  ║
║ 2. ISLRTC Gesture Dataset                                        ║
║    URL : https://islrtc.nic.in                                   ║
║    Type: Official Govt of India ISL dictionary                   ║
║    Note: Apply for academic access                               ║
║                                                                  ║
║ 3. Prayatna Dataset (Jadavpur University)                        ║
║    Type: 800+ isolated ISL words                                 ║
║    URL : Contact jadavpur.edu CS dept                            ║
║                                                                  ║
║ 4. YouTube ISL channels for bootstrap:                           ║
║    - "Sign Language India" channel                               ║
║    - "ISL Online" by NISH                                        ║
║    Tool: yt-dlp --format mp4 <url>                               ║
║                                                                  ║
║ 5. OpenHands (gesture synthesis, no videos needed):              ║
║    URL : https://github.com/ohadshe/OpenHands                    ║
║    Note: Skeleton-based ISL animation, MIT license               ║
║                                                                  ║
║ QUICKSTART: Run with --mode placeholder first.                   ║
║ Replace placeholder .mp4 files word-by-word with real clips.     ║
╚══════════════════════════════════════════════════════════════════╝
""")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AbleTab ISL Asset Manager")
    parser.add_argument("--mode", choices=["placeholder", "validate", "info"],
                        default="placeholder")
    parser.add_argument("--root", default="assets/gestures")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.mode == "placeholder":
        generate_placeholders(overwrite=args.overwrite)
        print("\nPlaceholder videos ready. Run main.py to test the avatar.")
    elif args.mode == "validate":
        ok = validate(args.root)
        sys.exit(0 if ok else 1)
    elif args.mode == "info":
        print_dataset_info()
