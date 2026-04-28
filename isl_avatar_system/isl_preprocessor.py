"""
isl_preprocessor.py
-------------------
Handles ISL-CSLRT dataset scanning, word-to-video mapping,
and fallback fingerspelling alphabet loading.

ISL-CSLRT is sentence-level, so we use it ONLY for reference
lookups (fuzzy sentence match). Primary mapping uses a small
hand-curated word dataset + fingerspelling fallback.
"""

import os
import json
import re
import glob
from pathlib import Path
from difflib import SequenceMatcher


# ──────────────────────────────────────────────
# PATHS  (edit these to match your folder layout)
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATASET_ROOT = BASE_DIR / "data"

WORD_VIDEO_DIR   = DATASET_ROOT / "word_signs"        # small custom word clips
ALPHA_VIDEO_DIR  = DATASET_ROOT / "fingerspelling"    # A-Z alphabet clips
CSLRT_VIDEO_DIR  = DATASET_ROOT / "isl_cslrt"        # sentence-level dataset
MAPPING_FILE     = DATASET_ROOT / "word_map.json"     # optional manual overrides


# ──────────────────────────────────────────────
# EXPECTED FOLDER STRUCTURE
# ──────────────────────────────────────────────
# data/
# ├── word_signs/
# │   ├── hello.mp4
# │   ├── yes.mp4
# │   ├── no.mp4
# │   ├── school.mp4
# │   ├── teacher.mp4   … etc.
# ├── fingerspelling/
# │   ├── a.mp4  b.mp4  … z.mp4
# ├── isl_cslrt/
# │   ├── sentence_001.mp4   (raw dataset clips)
# │   ├── sentence_002.mp4
# │   └── metadata.json      (labels for each clip)
# └── word_map.json           (optional overrides)


def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _video_exists(path: Path) -> bool:
    return path.exists() and path.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv")


# ──────────────────────────────────────────────
# 1. BUILD WORD → VIDEO MAP
# ──────────────────────────────────────────────

def build_word_map() -> dict:
    """
    Scans word_signs/ and returns {word: video_path}.
    Also loads any manual overrides from word_map.json.
    """
    word_map = {}

    # Auto-scan word_signs/
    if WORD_VIDEO_DIR.exists():
        for p in WORD_VIDEO_DIR.iterdir():
            if _video_exists(p):
                key = p.stem.lower().strip()
                word_map[key] = str(p)

    # Manual overrides
    overrides = _load_json(MAPPING_FILE)
    for word, rel_path in overrides.items():
        full = DATASET_ROOT / rel_path
        if _video_exists(full):
            word_map[word.lower()] = str(full)

    return word_map


# ──────────────────────────────────────────────
# 2. BUILD ALPHABET MAP  (fingerspelling)
# ──────────────────────────────────────────────

def build_alpha_map() -> dict:
    """Returns {'a': path, 'b': path, …} for fingerspelling."""
    alpha_map = {}
    if ALPHA_VIDEO_DIR.exists():
        for p in ALPHA_VIDEO_DIR.iterdir():
            if _video_exists(p) and len(p.stem) == 1:
                alpha_map[p.stem.lower()] = str(p)
    return alpha_map


# ──────────────────────────────────────────────
# 3. ISL-CSLRT SENTENCE REFERENCE LOOKUP
# ──────────────────────────────────────────────

def load_cslrt_metadata() -> dict:
    """
    Loads ISL-CSLRT metadata.json.
    Expected format:
      { "sentence_001": "I am going to school",
        "sentence_002": "What is your name", … }
    """
    meta_path = CSLRT_VIDEO_DIR / "metadata.json"
    return _load_json(meta_path)


def find_cslrt_match(sentence: str, metadata: dict,
                     threshold: float = 0.70) -> str | None:
    """
    Fuzzy-matches the input sentence against ISL-CSLRT labels.
    Returns the video path if similarity >= threshold, else None.
    This gives us REALISTIC sentence-level ISL when available.
    """
    sentence_clean = sentence.lower().strip()
    best_score = 0.0
    best_clip = None

    for clip_id, label in metadata.items():
        score = SequenceMatcher(None, sentence_clean,
                                label.lower().strip()).ratio()
        if score > best_score:
            best_score = score
            best_clip = clip_id

    if best_score >= threshold and best_clip:
        video_path = CSLRT_VIDEO_DIR / f"{best_clip}.mp4"
        if _video_exists(video_path):
            return str(video_path)
    return None


# ──────────────────────────────────────────────
# 4. PUBLIC API — ISLPreprocessor class
# ──────────────────────────────────────────────

class ISLPreprocessor:
    """
    One-stop initialiser.  Loads all maps once at startup.
    """

    def __init__(self):
        print("[Preprocessor] Building word map …")
        self.word_map   = build_word_map()
        self.alpha_map  = build_alpha_map()
        self.cslrt_meta = load_cslrt_metadata()

        print(f"[Preprocessor] Loaded {len(self.word_map)} word signs, "
              f"{len(self.alpha_map)} alphabet signs, "
              f"{len(self.cslrt_meta)} CSLRT sentences.")

    def get_word_video(self, word: str) -> str | None:
        return self.word_map.get(word.lower())

    def get_alpha_video(self, char: str) -> str | None:
        return self.alpha_map.get(char.lower())

    def get_cslrt_video(self, sentence: str) -> str | None:
        return find_cslrt_match(sentence, self.cslrt_meta)

    def coverage_report(self, words: list[str]) -> dict:
        """Returns which words have direct coverage vs fingerspelling only."""
        report = {"direct": [], "fingerspell": [], "missing_letters": []}
        for w in words:
            if self.get_word_video(w):
                report["direct"].append(w)
            else:
                missing = [c for c in w if c.isalpha()
                           and not self.get_alpha_video(c)]
                if missing:
                    report["missing_letters"].extend(missing)
                else:
                    report["fingerspell"].append(w)
        return report


# Quick self-test
if __name__ == "__main__":
    pre = ISLPreprocessor()
    test_words = ["hello", "school", "xyz123"]
    print(pre.coverage_report(test_words))
