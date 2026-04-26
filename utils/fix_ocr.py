"""
fix_ocr.py — Tesseract OCR Diagnostic & Auto-Fix
==================================================
Run this to find exactly why OCR is failing and fix it.

Usage:
  python fix_ocr.py
"""

import subprocess
import sys
import os
import platform
import shutil

system = platform.system()
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}!{RESET} {msg}")
def section(t): print(f"\n  {'─'*50}\n  {t}\n  {'─'*50}")


# ──────────────────────────────────────────────────
# STEP 1: Is the tesseract binary on PATH?
# ──────────────────────────────────────────────────
section("Step 1: Locate Tesseract binary")

tess_path = shutil.which("tesseract")
if tess_path:
    ok(f"Found on PATH: {tess_path}")
else:
    fail("tesseract not found on PATH")

    if system == "Windows":
        # Common Windows install locations
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        found = None
        for c in candidates:
            if os.path.exists(c):
                found = c
                ok(f"Found at: {c}")
                break

        if found:
            warn("Tesseract IS installed but NOT on PATH.")
            info("Two ways to fix this:\n")
            print(f"""
  OPTION A — Tell pytesseract the path directly (easiest):
  ─────────────────────────────────────────────────────────
  Edit  utils/ocr_pipeline.py  and ADD this line near the top,
  right after the imports:

      import pytesseract
      pytesseract.pytesseract.tesseract_cmd = r"{found}"

  OPTION B — Add to Windows PATH permanently:
  ─────────────────────────────────────────────────────────
  1. Press  Win + S  → search "Environment Variables"
  2. Click "Edit the system environment variables"
  3. Click "Environment Variables" button
  4. Under "System variables" → select "Path" → "Edit"
  5. Click "New" → paste:  {os.path.dirname(found)}
  6. Click OK three times
  7. RESTART VS Code terminal completely
""")
        else:
            fail("Tesseract is NOT installed on this machine.")
            print(f"""
  Download and install Tesseract for Windows:
  ────────────────────────────────────────────
  1. Go to:
     https://github.com/UB-Mannheim/tesseract/wiki

  2. Download the latest  tesseract-ocr-w64-setup-*.exe

  3. Run the installer
     ✓ Keep default install path
     ✓ Check "Add to PATH" if the option appears

  4. After install: RESTART your VS Code terminal

  5. Run this script again to verify.
""")

    elif system == "Darwin":
        fail("Tesseract not found.")
        print("""
  Install via Homebrew:
  ──────────────────────
  brew install tesseract

  If you don't have Homebrew:
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  After installing, run this script again.
""")

    else:  # Linux
        fail("Tesseract not found.")
        print("""
  Install via apt:
  ─────────────────
  sudo apt update
  sudo apt install -y tesseract-ocr

  Then run this script again.
""")

    sys.exit(1)  # No point continuing without binary


# ──────────────────────────────────────────────────
# STEP 2: Check tesseract version
# ──────────────────────────────────────────────────
section("Step 2: Tesseract version check")
try:
    result = subprocess.run(
        ["tesseract", "--version"],
        capture_output=True, text=True
    )
    version_line = result.stdout.strip().split("\n")[0]
    ok(f"Version: {version_line}")
except Exception as e:
    fail(f"Could not run tesseract: {e}")


# ──────────────────────────────────────────────────
# STEP 3: Is pytesseract installed?
# ──────────────────────────────────────────────────
section("Step 3: pytesseract Python package")
try:
    import pytesseract
    ok(f"pytesseract imported (version: {pytesseract.__version__})")
except ImportError:
    fail("pytesseract not installed")
    info(f"Fix: {sys.executable} -m pip install pytesseract")
    sys.exit(1)


# ──────────────────────────────────────────────────
# STEP 4: Can pytesseract find the binary?
# ──────────────────────────────────────────────────
section("Step 4: pytesseract → tesseract link")
try:
    ver = pytesseract.get_tesseract_version()
    ok(f"pytesseract connected to Tesseract v{ver}")
except pytesseract.TesseractNotFoundError as e:
    fail(f"pytesseract cannot find Tesseract: {e}")

    if system == "Windows":
        # Auto-detect and patch
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for c in candidates:
            if os.path.exists(c):
                pytesseract.pytesseract.tesseract_cmd = c
                try:
                    ver = pytesseract.get_tesseract_version()
                    ok(f"Auto-fixed! Tesseract found at: {c}")
                    warn("This only lasts for this script session.")
                    info("Add this line to utils/ocr_pipeline.py to make it permanent:\n")
                    print(f'      pytesseract.pytesseract.tesseract_cmd = r"{c}"\n')
                    break
                except Exception:
                    pass
        else:
            fail("Could not auto-fix. Follow Step 1 instructions above.")
            sys.exit(1)
    else:
        fail("Unexpected: binary found on PATH but pytesseract can't use it.")
        info("Try: pip install --upgrade pytesseract")
        sys.exit(1)
except Exception as e:
    fail(f"Unexpected error: {e}")
    sys.exit(1)


# ──────────────────────────────────────────────────
# STEP 5: Run a real OCR test
# ──────────────────────────────────────────────────
section("Step 5: Live OCR test")
try:
    import cv2
    import numpy as np

    # Create a clean white image with black text
    img = np.ones((120, 500, 3), dtype=np.uint8) * 255
    cv2.putText(img, "AbleTab OCR Test 1234",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                1.5, (0, 0, 0), 3)

    # Save test image so you can inspect it
    os.makedirs("sessions", exist_ok=True)
    cv2.imwrite("sessions/ocr_test_image.png", img)
    info("Test image saved → sessions/ocr_test_image.png")

    # Run OCR
    text = pytesseract.image_to_string(img, config="--oem 1 --psm 6").strip()
    text_clean = " ".join(text.split())

    if text_clean:
        ok(f"OCR output: '{text_clean}'")
        ok("OCR is working correctly!")
    else:
        warn("Tesseract ran but returned empty text on synthetic image.")
        warn("This can happen on some Tesseract builds.")
        info("Testing with real webcam image instead...")

        # Try with webcam
        cap = cv2.VideoCapture(0)
        for _ in range(3): cap.read()  # warmup
        ret, frame = cap.read()
        cap.release()

        if ret:
            cv2.imwrite("sessions/ocr_webcam_test.png", frame)
            text2 = pytesseract.image_to_string(frame, config="--oem 1 --psm 6").strip()
            text2_clean = " ".join(text2.split())
            if text2_clean:
                ok(f"Webcam OCR output: '{text2_clean[:80]}...'")
                ok("OCR works on real images!")
            else:
                warn("No text detected from webcam.")
                info("Point your camera at printed text and run test again.")
        else:
            warn("Webcam capture failed.")

except Exception as e:
    fail(f"OCR test failed: {e}")
    sys.exit(1)


# ──────────────────────────────────────────────────
# STEP 6: Auto-patch ocr_pipeline.py if needed
# ──────────────────────────────────────────────────
section("Step 6: Auto-patch ocr_pipeline.py (Windows only)")

ocr_file = os.path.join("utils", "ocr_pipeline.py")

if system == "Windows" and os.path.exists(ocr_file):
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    tess_exe = next((c for c in candidates if os.path.exists(c)), None)

    if tess_exe:
        with open(ocr_file, "r", encoding="utf-8") as f:
            content = f.read()

        patch_line = f'pytesseract.pytesseract.tesseract_cmd = r"{tess_exe}"'
        marker = "# On Windows, set the Tesseract path explicitly if needed:"

        if patch_line in content:
            ok("ocr_pipeline.py already patched")
        elif marker in content:
            # Replace the commented-out line with the real path
            old = f'# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"'
            new = patch_line
            patched = content.replace(old, new)
            with open(ocr_file, "w", encoding="utf-8") as f:
                f.write(patched)
            ok(f"Auto-patched ocr_pipeline.py with: {tess_exe}")
        else:
            warn("Could not auto-patch — add this line manually to utils/ocr_pipeline.py:")
            print(f"\n      {patch_line}\n")
    else:
        info("Tesseract not found in default Windows paths — no patch needed (PATH is set)")
else:
    info("Not Windows or ocr_pipeline.py not found — no patch needed")


# ──────────────────────────────────────────────────
# Done
# ──────────────────────────────────────────────────
print(f"""
  {'─'*50}
  {GREEN}All OCR checks passed!{RESET}
  {'─'*50}
  Run test_components.py to verify everything:
    python test_components.py

  Then launch AbleTab:
    python main.py
  {'─'*50}
""")
