"""
modes/revision.py - Revision Mode (Laptop Version)
====================================================
Designed for blind students — fully voice + keyboard accessible.

Flow:
  1. Automatically loads the latest session (or lets user pick)
  2. Announces what's available (audio count, notes word count)
  3. Waits for one of 5 commands:
       "read notes"  → reads notes aloud in short chunks
       "play audio"  → plays current WAV file
       "next"        → advance to next audio chunk
       "repeat"      → repeats last action
       "exit"        → exits revision mode
  4. Gives voice confirmation after every action
  5. Returns to command prompt

Audio playback (laptop):
  - Windows → uses winsound or pygame
  - macOS   → uses afplay (built-in)
  - Linux   → uses aplay (built-in)
"""

import os
import time
import sys
import platform
import subprocess

from utils.tts import speak, speak_slow
from utils.session import (
    get_all_sessions,
    get_latest_session,
    get_audio_files,
    get_notes_text
)

PAUSE = 0.5   # Short pause between TTS messages


def run_revision():
    """Entry point for Revision Mode."""

    _print_banner()

    # Select session
    session_path = _select_session()
    if not session_path:
        speak("No sessions found. Please record a class first.")
        print("\n  No sessions found in the sessions/ folder.")
        print("  Run Live Class Mode first to create a session.\n")
        return

    # Load data
    audio_files = get_audio_files(session_path)
    notes_text = get_notes_text(session_path)

    # State
    state = {
        "audio_index": 0,
        "last_action": None,
    }

    # Announce what's available
    _announce_session(session_path, audio_files, notes_text)

    # Command loop
    _print_command_help()
    speak("Ready. Give a command.")

    while True:
        command = _get_command()

        if command is None:
            speak("Command not recognized. Try again.")
            continue

        should_exit = _execute_command(command, state, audio_files, notes_text)
        if should_exit:
            break

        time.sleep(PAUSE)

    speak("Goodbye.")
    print("\n  [Revision Mode]: Exited.\n")


# -----------------------------------------------
# Session Selection
# -----------------------------------------------

def _select_session():
    """
    Show available sessions in terminal.
    Auto-select latest, or let user pick by number.
    """
    sessions = get_all_sessions()
    if not sessions:
        return None

    if len(sessions) == 1:
        print(f"\n  Loading only session: {os.path.basename(sessions[0])}")
        speak("Loading your session.")
        return sessions[0]

    # Multiple sessions — show a list
    print("\n  Available Sessions:")
    for i, s in enumerate(sessions[:5]):  # Show max 5
        name = os.path.basename(s)
        audio_count = len(get_audio_files(s))
        print(f"    [{i+1}] {name}  ({audio_count} audio files)")

    speak(f"Found {len(sessions)} sessions. Press Enter to load the latest.")
    choice = input("\n  Select session number (Enter = latest): ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            return sessions[idx]
    except ValueError:
        pass

    return sessions[0]  # Default: latest


# -----------------------------------------------
# Session Announcement
# -----------------------------------------------

def _announce_session(session_path, audio_files, notes_text):
    """Tell the user what's in this session."""
    folder = os.path.basename(session_path)

    print(f"\n  Session: {folder}")
    print(f"  Audio files : {len(audio_files)}")
    print(f"  Notes words : {len(notes_text.split()) if notes_text else 0}")
    print()

    time.sleep(0.3)
    if audio_files:
        speak(f"{len(audio_files)} audio recordings available.")
    else:
        speak("No audio recordings in this session.")

    if notes_text:
        speak(f"Notes have {len(notes_text.split())} words.")
    else:
        speak("No notes available.")
    time.sleep(0.3)


# -----------------------------------------------
# Command Input
# -----------------------------------------------

def _get_command():
    """
    Get a command via voice or keyboard.
    Both methods run in parallel — first result wins.
    """
    from utils.voice_input import listen_once
    return listen_once(timeout=8)


# -----------------------------------------------
# Command Execution
# -----------------------------------------------

def _execute_command(command, state, audio_files, notes_text):
    """
    Run the given command. Returns True to exit, False to continue.
    """
    print(f"\n  → Command: [{command}]")

    if command == "read notes":
        _cmd_read_notes(notes_text, state)

    elif command == "play audio":
        _cmd_play_audio(audio_files, state)

    elif command == "next":
        _cmd_next(audio_files, state)

    elif command == "repeat":
        _cmd_repeat(state, audio_files, notes_text)

    elif command == "exit":
        return True

    return False


def _cmd_read_notes(notes_text, state):
    if not notes_text:
        speak("No notes to read.")
        print("  [Notes]: Empty")
        return

    speak("Reading notes now.")
    time.sleep(0.4)

    # Split notes into manageable 25-word chunks
    chunks = _split_into_chunks(notes_text, max_words=25)
    total = len(chunks)

    print(f"\n  [Notes]: Reading {total} chunk(s)...\n")
    print("  " + "─" * 40)

    for i, chunk in enumerate(chunks, 1):
        print(f"  [{i}/{total}] {chunk}")
        speak_slow(chunk)
        time.sleep(0.4)

    print("  " + "─" * 40)
    speak("End of notes.")
    state["last_action"] = "read notes"


def _cmd_play_audio(audio_files, state):
    if not audio_files:
        speak("No audio files available.")
        return

    idx = state["audio_index"]
    if idx >= len(audio_files):
        speak("You have reached the last recording.")
        return

    filepath = audio_files[idx]
    filename = os.path.basename(filepath)
    chunk_num = idx + 1
    total = len(audio_files)

    print(f"\n  [Audio]: Playing {filename} ({chunk_num}/{total})")
    speak(f"Playing recording {chunk_num} of {total}.")
    time.sleep(0.3)

    _play_audio_file(filepath)

    speak("Playback complete.")
    state["last_action"] = "play audio"


def _cmd_next(audio_files, state):
    if not audio_files:
        speak("No audio files.")
        return

    idx = state["audio_index"]
    if idx + 1 >= len(audio_files):
        speak("This is the last recording. No more files.")
        print("  [Audio]: Already at last chunk.")
        return

    state["audio_index"] = idx + 1
    new_num = state["audio_index"] + 1
    total = len(audio_files)

    print(f"  [Audio]: Moved to chunk {new_num}/{total}")
    speak(f"Now on recording {new_num} of {total}.")
    state["last_action"] = "next"


def _cmd_repeat(state, audio_files, notes_text):
    last = state.get("last_action")
    if last is None:
        speak("Nothing to repeat yet.")
        return

    speak("Repeating.")
    time.sleep(0.3)

    if last == "read notes":
        _cmd_read_notes(notes_text, state)
    elif last in ("play audio", "next"):
        _cmd_play_audio(audio_files, state)


# -----------------------------------------------
# Cross-Platform Audio Playback
# -----------------------------------------------

def _play_audio_file(filepath):
    """
    Play a WAV file using the best available method for the OS.
    Works on Windows, macOS, and Linux without extra dependencies.
    """
    system = platform.system()

    try:
        if system == "Windows":
            _play_windows(filepath)
        elif system == "Darwin":   # macOS
            _play_macos(filepath)
        else:                      # Linux
            _play_linux(filepath)
    except Exception as e:
        print(f"  [Audio Playback Error]: {e}")
        speak("Could not play audio file.")


def _play_windows(filepath):
    """Windows: use winsound (built-in, no install needed)."""
    import winsound
    winsound.PlaySound(filepath, winsound.SND_FILENAME)


def _play_macos(filepath):
    """macOS: use afplay command (built-in)."""
    subprocess.run(["afplay", filepath], check=True)


def _play_linux(filepath):
    """Linux: use aplay (ALSA, built-in on most distros)."""
    subprocess.run(["aplay", filepath], check=True)


# -----------------------------------------------
# Helpers
# -----------------------------------------------

def _split_into_chunks(text, max_words=25):
    """Break text into word-limited chunks for comfortable TTS listening."""
    words = text.split()
    return [
        " ".join(words[i:i + max_words])
        for i in range(0, len(words), max_words)
    ]


def _print_banner():
    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║       AbleTab — REVISION MODE            ║")
    print("  ║     (Voice + Keyboard Navigation)        ║")
    print("  ╚══════════════════════════════════════════╝")


def _print_command_help():
    print("\n  ┌──────────────────────────────────────────┐")
    print("  │  Available Commands                      │")
    print("  ├──────────────────────────────────────────┤")
    print("  │  Say or type:                            │")
    print("  │    'read notes'  → hear your notes       │")
    print("  │    'play audio'  → play current recording│")
    print("  │    'next'        → next recording        │")
    print("  │    'repeat'      → repeat last action    │")
    print("  │    'exit'        → quit                  │")
    print("  └──────────────────────────────────────────┘\n")
