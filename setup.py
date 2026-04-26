#!/usr/bin/env python3
"""
setup.py — AbleTab Laptop Setup Script
========================================
Run this ONCE to install all Python dependencies.
Cross-platform: works on Windows, macOS, Linux.

Usage:
  python setup.py
"""

import subprocess
import sys
import platform
import os


def run(cmd, label):
    print(f"\n  [{label}]")
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode == 0:
        print(f"  ✓ Done")
    else:
        print(f"  ✗ Failed (exit code {result.returncode})")
    return result.returncode == 0


def main():
    system = platform.system()
    python = sys.executable

    print("╔══════════════════════════════════════════╗")
    print("║       AbleTab — Laptop Setup             ║")
    print(f"║  Platform: {system:<31}║")
    print(f"║  Python:   {sys.version.split()[0]:<31}║")
    print("╚══════════════════════════════════════════╝\n")

    # ── Step 1: Upgrade pip ────────────────────────
    run([python, "-m", "pip", "install", "--upgrade", "pip"],
        "Upgrading pip")

    # ── Step 2: Install Python packages ───────────
    packages = [
        "pyttsx3",
        "SpeechRecognition",
        "sounddevice",
        "scipy",
        "opencv-python",
        "pytesseract",
        "numpy",
    ]
    for pkg in packages:
        run([python, "-m", "pip", "install", pkg], f"Installing {pkg}")

    # ── Step 3: System-level instructions ─────────
    print("\n  ─────────────────────────────────────────")
    print("  IMPORTANT: Install Tesseract (system tool)")
    print("  ─────────────────────────────────────────")

    if system == "Windows":
        print("""
  1. Download Tesseract installer:
     https://github.com/UB-Mannheim/tesseract/wiki

  2. Run the installer (accept all defaults)

  3. Add Tesseract to PATH:
     System Properties → Environment Variables →
     Path → Add → C:\\Program Files\\Tesseract-OCR

  4. Restart VS Code terminal after adding to PATH
""")
    elif system == "Darwin":
        print("""
  Run in terminal:
    brew install tesseract

  If you don't have brew:
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
""")
    else:  # Linux
        print("""
  Run in terminal:
    sudo apt update
    sudo apt install -y tesseract-ocr alsa-utils espeak
""")

    # ── Step 4: Create sessions folder ────────────
    os.makedirs("sessions", exist_ok=True)
    print("  ✓ sessions/ folder created")

    # ── Step 5: Final instructions ────────────────
    print("\n  ─────────────────────────────────────────")
    print("  Setup complete! Next steps:")
    print("  ─────────────────────────────────────────")
    print("  1. Install Tesseract (see instructions above)")
    print("  2. Run tests:  python test_components.py")
    print("  3. Launch app: python main.py")
    print("  ─────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
