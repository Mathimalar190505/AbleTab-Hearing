"""
utils/session.py - Session Folder Management
=============================================
Creates and manages session folders containing:
  audio/    → .wav chunks of recorded lecture
  images/   → webcam snapshots for OCR
  notes.txt → extracted text from OCR

Folder name example:
  sessions/session_2024-01-15_09-30-00/
"""

import os
from datetime import datetime

# All sessions stored relative to the project root
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")


def create_session_folder():
    """Create a timestamped session folder. Returns path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_path = os.path.join(BASE_DIR, f"session_{timestamp}")

    os.makedirs(os.path.join(session_path, "audio"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "images"), exist_ok=True)

    # Initialize notes file with header
    with open(os.path.join(session_path, "notes.txt"), "w", encoding="utf-8") as f:
        f.write(f"AbleTab Notes — {timestamp}\n")
        f.write("=" * 40 + "\n\n")

    print(f"\n  [Session]: Created → {session_path}")
    return session_path


def get_all_sessions():
    """Return all session paths, newest first."""
    if not os.path.exists(BASE_DIR):
        return []
    paths = [
        os.path.join(BASE_DIR, d)
        for d in sorted(os.listdir(BASE_DIR), reverse=True)
        if d.startswith("session_") and os.path.isdir(os.path.join(BASE_DIR, d))
    ]
    return paths


def get_latest_session():
    """Return the most recent session path, or None."""
    sessions = get_all_sessions()
    return sessions[0] if sessions else None


def get_audio_files(session_path):
    """Return sorted list of .wav files in session's audio/ folder."""
    audio_dir = os.path.join(session_path, "audio")
    if not os.path.exists(audio_dir):
        return []
    return sorted([
        os.path.join(audio_dir, f)
        for f in os.listdir(audio_dir)
        if f.endswith(".wav")
    ])


def get_notes_path(session_path):
    return os.path.join(session_path, "notes.txt")


def get_notes_text(session_path):
    """Read and return full notes.txt content."""
    path = get_notes_path(session_path)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def append_to_notes(session_path, text):
    """Append OCR-extracted text to notes.txt with timestamp."""
    path = get_notes_path(session_path)
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n[{timestamp}]\n{text.strip()}\n")
    print(f"  [Notes]: +{len(text)} chars saved")
