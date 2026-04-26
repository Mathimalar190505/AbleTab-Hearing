# AbleTab — Laptop Prototype

Runs entirely on your laptop in VS Code terminal.
No Raspberry Pi, no ESP32-CAM, no external hardware needed.

---

## What Replaces What

| Raspberry Pi Version | Laptop Version |
|---|---|
| Raspberry Pi Zero 2 W | Your laptop |
| ESP32-CAM | Laptop webcam (`cv2.VideoCapture(0)`) |
| USB microphone | Laptop built-in mic |
| Physical speaker | Laptop speakers |
| `aplay` (ALSA) | `winsound` / `afplay` / `aplay` |

---

## Project Structure

```
abletab_laptop/
│
├── main.py                  ← Start here
│
├── modes/
│   ├── live_class.py        ← Record audio + OCR in parallel
│   └── revision.py          ← Voice/keyboard navigation
│
├── utils/
│   ├── tts.py               ← pyttsx3 (offline, cross-platform)
│   ├── voice_input.py       ← Mic + keyboard dual-input
│   ├── audio_recorder.py    ← sounddevice / pyaudio chunked recording
│   ├── ocr_pipeline.py      ← Webcam → preprocess → Tesseract
│   ├── session.py           ← Timestamped folder management
│   └── braille.py           ← Braille dot patterns (visual simulation)
│
├── sessions/                ← Created automatically on first run
│   └── session_YYYY-MM-DD_HH-MM-SS/
│       ├── audio/           ← chunk_001.wav, chunk_002.wav ...
│       ├── images/          ← img_001.jpg, img_002.jpg ...
│       └── notes.txt        ← OCR-extracted text
│
├── setup.py                 ← One-click install script
├── test_components.py       ← Verify hardware + libraries
└── requirements.txt         ← Python dependencies
```

---

## Quick Start (3 steps)

### Step 1 — Install Python packages

```bash
python setup.py
```

Or manually:
```bash
pip install -r requirements.txt
```

### Step 2 — Install Tesseract (required for OCR)

**Windows:**
- Download from https://github.com/UB-Mannheim/tesseract/wiki
- Run installer → Add `C:\Program Files\Tesseract-OCR` to PATH
- Restart terminal

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr alsa-utils espeak
```

### Step 3 — Verify and run

```bash
# Verify all components
python test_components.py

# Run AbleTab
python main.py
```

---

## How to Use Each Mode

### Mode 1: Live Class Mode

1. Press `1` when prompted
2. AbleTab starts:
   - Recording your mic → `sessions/.../audio/chunk_001.wav`
   - Capturing webcam every 12s → OCR → `notes.txt`
3. Press **Enter** in terminal to stop
4. A session summary is printed and spoken

**Tip for testing:** Point your webcam at a printed page or book to test OCR.

### Mode 2: Revision Mode

1. Press `2` when prompted
2. AbleTab loads the latest session
3. Use voice OR keyboard to navigate:

| Say / Type | Action |
|---|---|
| `read notes` | Reads notes.txt aloud |
| `play audio` | Plays current audio chunk |
| `next` | Moves to next audio chunk |
| `repeat` | Repeats the last action |
| `exit` | Exits revision mode |

**Keyboard shortcuts:** `r` = repeat, `n` = next, `q` = exit

---

## Troubleshooting

### "Tesseract not found"
- Windows: Re-check PATH and restart VS Code terminal
- macOS: Run `which tesseract` — if empty, re-install via brew
- Linux: Run `tesseract --version`

### "No audio devices found"
- Check laptop mic is not muted in system settings
- Check mic permissions (especially macOS — allow Terminal/VS Code)

### "Webcam not accessible"
- Another app (Zoom, Teams) may be using it — close them first
- On macOS: System Preferences → Security & Privacy → Camera → allow Terminal

### "pyttsx3 not speaking" on Linux
```bash
sudo apt install espeak
```

### Voice commands not recognized
- Check internet connection (Google STT needs it)
- Or just type the command — keyboard fallback always works

---

## Notes on Internet Dependency

| Feature | Online? | Offline fallback |
|---|---|---|
| Voice recognition (Google STT) | ✓ Yes | Keyboard input |
| Voice recognition (Sphinx) | ✗ No | Built-in (less accurate) |
| TTS (pyttsx3) | ✗ No | Always offline |
| OCR (Tesseract) | ✗ No | Always offline |
| Audio recording | ✗ No | Always offline |

AbleTab works fully offline — voice recognition just degrades to keyboard input without internet.
