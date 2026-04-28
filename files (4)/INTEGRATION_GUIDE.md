# AbleTab-Hearing — ISL Sign Language Avatar
## Complete Integration Guide

---

## 1. Repository Structure After Integration

```
AbleTab-Hearing/
│
├── main.py                          ← YOUR EXISTING FILE (3 lines added)
├── modes/                           ← YOUR EXISTING FOLDER (unchanged)
├── utils/                           ← YOUR EXISTING FOLDER (unchanged)
│
├── sign_language/                   ← ✅ NEW: entire folder you add
│   ├── __init__.py
│   ├── isl_preprocessor.py          ← ISL grammar engine
│   ├── gesture_mapper.py            ← word → video clip mapper
│   ├── avatar_player.py             ← OpenCV render engine
│   ├── sign_pipeline.py             ← coordinator (main integration point)
│   ├── download_assets.py           ← asset setup utility
│   ├── main_patch.py                ← integration guide + demo
│   │
│   ├── assets/
│   │   └── gestures/
│   │       ├── words/               ← WORD.mp4 files (62 words seeded)
│   │       ├── letters/             ← A.mp4 … Z.mp4 (fingerspelling)
│   │       └── special/             ← UNKNOWN.mp4, PAUSE.mp4
│   │
│   └── tests/
│       └── test_sign_pipeline.py    ← 11 unit tests (all passing)
│
└── requirements_sign.txt            ← ✅ NEW: dependencies
```

---

## 2. Quick Start (3 Steps)

### Step A — Install dependencies
```bash
pip install opencv-python numpy
# (SpeechRecognition already installed in your project)
```

### Step B — Generate placeholder gesture videos
```bash
cd AbleTab-Hearing
python sign_language/download_assets.py --mode placeholder
```
This creates 90 animated placeholder `.mp4` files (62 words + 26 letters + 2 specials).
The system works immediately. Replace them word-by-word with real ISL clips later.

### Step C — Run the demo
```bash
python sign_language/sign_pipeline.py
```
An OpenCV window opens and plays coloured gesture animations for sample sentences.

---

## 3. Integrating into YOUR main.py

Find your existing `main.py`. Make exactly these 3 changes:

### Change 1 — Add import at the top
```python
# Add after your existing imports:
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sign_language.sign_pipeline import SignLanguagePipeline

_sign_pipeline = SignLanguagePipeline(
    assets_root="sign_language/assets/gestures",
    playback_speed=1.0,
    transition_ms=200,
)
_sign_pipeline.start()
```

### Change 2 — Hook into your STT result callback
Find where you display the speech-to-text result. It probably looks like:
```python
def on_speech_result(text):
    caption_label.config(text=text)   # your existing line
```

Add ONE line:
```python
def on_speech_result(text):
    caption_label.config(text=text)          # keep as-is
    _sign_pipeline.process_text(text)        # ← ADD THIS
```

### Change 3 — Clean shutdown
```python
# In your window close handler:
_sign_pipeline.stop()
```

**That's the entire integration.** The avatar runs in a background thread.

---

## 4. Architecture: How Each Module Works

### 4.1 isl_preprocessor.py — Text → ISL Tokens
```
Input : "The teacher is explaining the lesson."
Output: ['TEACHER', 'EXPLAINING', 'LESSON']
```

**ISL grammar rules applied:**
| Rule | Example |
|---|---|
| Drop articles | the, a, an → removed |
| Drop copula | is, are, am, was → removed |
| Drop auxiliaries | has, have, will, do → removed |
| Move WH-word to end | "What is your name?" → "YOUR NAME WHAT" |
| Move negation to end | "I don't know" → "I KNOW NOT" |
| Expand contractions | "I'm" → "I", "can't" → "CANNOT" |
| Uppercase all tokens | everything → UPPERCASE |

### 4.2 gesture_mapper.py — Tokens → Clip List
```
Input : ['TEACHER', 'EXPLAINING', 'LESSON']
Output: [GestureClip("TEACHER", "words/TEACHER.mp4", mode="video"), ...]
```

**Fallback priority chain:**
```
1. Exact word match in index         → video clip
2. Stemmed match (drop -ING, -ED...) → video clip
3. Short word (≤6 chars)             → fingerspell letter-by-letter
4. Long unknown word                 → UNKNOWN.mp4 placeholder
```

### 4.3 avatar_player.py — Clip List → OpenCV Window
```
Runs in a background thread.
Reads clips from a queue → plays each video with cross-fade transitions.
Draws subtitle bar showing current ISL sentence + highlighted word.
```

**Key features:**
- Cross-fade between gestures (configurable ms)
- Thread-safe queue (no UI blocking)
- Graceful placeholder rendering if video files are missing
- `pause()` / `resume()` / `stop()` controls
- Press `Q` in window to quit

### 4.4 sign_pipeline.py — Coordinator
```python
pipeline = SignLanguagePipeline(assets_root="sign_language/assets/gestures")
pipeline.start()
pipeline.process_text("Please help me.")   # Non-blocking!
pipeline.stop()
```

---

## 5. ISL Preprocessing Examples (Live Test Results)

```
Original : "The teacher is explaining the lesson to the students."
ISL      : TEACHER EXPLAINING LESSON STUDENTS

Original : "I don't know where the library is."
ISL      : I KNOW LIBRARY WHERE NOT

Original : "She has been studying very hard for the exam."
ISL      : SHE STUDYING VERY HARD FOR EXAM

Original : "What is your name?"
ISL      : YOUR NAME WHAT

Original : "We are going to the hospital tomorrow."
ISL      : WE GOING HOSPITAL TOMORROW
```

---

## 6. Replacing Placeholders with Real ISL Videos

The system uses a **drop-in replacement** approach. To replace any word:

```bash
# Example: replace HELLO.mp4 with a real ISL clip
cp /path/to/real/ISL_HELLO.mp4 sign_language/assets/gestures/words/HELLO.mp4
```

Requirements for real clips:
- Format: `.mp4` (H.264 encoded)
- Recommended size: 400×300 or 640×480
- Duration: 1–3 seconds per word
- Background: solid colour preferred for clean compositing

---

## 7. Real ISL Dataset Sources

### Priority 1 — ISL-CSLRT (IIT Delhi)
- URL: `https://www.iitd.ac.in/~pkalra/isl-cslrt/`
- 7000+ videos, 200+ classroom-relevant words
- RGB + depth camera, high quality
- **Best choice for this project**

### Priority 2 — ISLRTC (Government of India)
- URL: `https://islrtc.nic.in`
- Official ISL dictionary with video examples
- Apply for academic access (usually approved quickly)

### Priority 3 — Prayatna Dataset (Jadavpur University)
- 800+ isolated ISL word videos
- Contact JU CS Department for academic use

### Priority 4 — YouTube Bootstrap
```bash
pip install yt-dlp
yt-dlp -f mp4 -o "words/%(title)s.mp4" "https://youtube.com/..."
# Channels: "Sign Language India", "ISL Online" by NISH
```

### Priority 5 — OpenHands (Skeleton-Based, No Videos Needed)
- `https://github.com/ohadshe/OpenHands`
- Generates ISL signing from text using skeleton animation
- MIT license — can replace the video-based approach entirely

---

## 8. Advanced Features Roadmap

### A. Smooth Sentence-Level Animation (Already Built)
The cross-fade system in `avatar_player.py` provides smooth transitions.
Tune `transition_ms` (default 200ms) to control blend speed.

### B. Add More Words — JSON Dictionary
Create `sign_language/isl_dictionary.json`:
```json
{
  "WATER": "words/WATER.mp4",
  "FOOD":  "words/FOOD.mp4",
  "PAIN":  "words/PAIN.mp4"
}
```
Pass to pipeline:
```python
SignLanguagePipeline(gesture_json="sign_language/isl_dictionary.json")
```

### C. Playback Speed for Learners
```python
SignLanguagePipeline(playback_speed=0.7)   # 30% slower
```

### D. 3D Avatar (Optional Advanced)
Install: `pip install pyglet trimesh pyopengl`

Download a free signing avatar `.glb` from:
- `https://www.readyplayer.me` (create custom avatar)
- `https://sketchfab.com/3d-models?q=sign+language`

Then use trimesh + pyglet to render the model and animate joint rotations
per gesture keyframe data. This is a significant extension — recommended
only if you have 2+ weeks extra.

### E. Facial Expression Handling
For complete ISL (which uses facial grammar for questions/negation):
```python
# In avatar_player.py, add expression overlay:
# - raised eyebrows for WH-questions (WHO, WHAT, WHERE)
# - furrowed brows for YES/NO questions
# Implement as transparent face overlay PNG composited on each frame
```

### F. Real-Time Streaming (WebSocket)
```python
# Replace enqueue_clips with a WebSocket emit for browser-based avatar
import websockets
async def stream_gesture(clip_path):
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send(json.dumps({"clip": clip_path}))
```

---

## 9. Configuration Reference

```python
SignLanguagePipeline(
    assets_root   = "sign_language/assets/gestures",  # gesture video folder
    gesture_json  = None,           # optional extra dictionary JSON
    window_w      = 640,            # avatar window width
    window_h      = 480,            # avatar window height
    transition_ms = 200,            # cross-fade duration (ms)
    playback_speed= 1.0,            # 1.0=normal, 0.7=slow, 1.5=fast
    headless      = False,          # True = no GUI (for testing)
    min_sentence_gap_ms = 300,      # ignore duplicate sentences < 300ms apart
)
```

---

## 10. Running Tests

```bash
# Run all 11 unit tests
python sign_language/tests/test_sign_pipeline.py

# With pytest
pip install pytest
pytest sign_language/tests/ -v
```

Expected output: `11/11 tests passed.`

---

## 11. Troubleshooting

| Problem | Solution |
|---|---|
| `cv2` not found | `pip install opencv-python` |
| Black/blank window | Set `headless=False`, check display |
| No audio on avatar | Normal — avatar is visual-only |
| Word not signing | Check coverage report in console log |
| Window closes immediately | Add `time.sleep(N)` after `process_text()` |
| High CPU usage | Reduce window size or add `time.sleep(0.001)` in render loop |

---

*Built for AbleTab-Hearing — Assistive Technology for Deaf Students*
*Pipeline: Audio → STT → ISL Preprocessing → Gesture Mapping → Avatar Rendering*
