"""
utils/audio_recorder.py - Chunked Audio Recording (Laptop Version)
====================================================================
Records from the laptop's built-in microphone.
Saves audio in 10-minute WAV chunks.

Uses sounddevice + scipy (more reliable on Windows/macOS than pyaudio).
Falls back to pyaudio if sounddevice is unavailable.

Install:
  pip install sounddevice scipy
  OR
  pip install pyaudio
"""

import os
import wave
import threading
import time
import struct
from datetime import datetime

# Audio settings
SAMPLE_RATE = 16000      # 16kHz — good for speech, small files
CHANNELS = 1             # Mono
CHUNK_DURATION = 10 * 60 # 10 minutes per chunk (in seconds)
DTYPE = 'int16'          # 16-bit PCM


class AudioRecorder:
    """Records audio in background thread, saving WAV chunks."""

    def __init__(self, session_path, chunk_duration=CHUNK_DURATION):
        self.session_path = session_path
        self.audio_dir = os.path.join(session_path, "audio")
        self.chunk_duration = chunk_duration
        self.is_recording = False
        self._thread = None
        self._chunk_count = 0
        self._use_sounddevice = self._check_sounddevice()

    def _check_sounddevice(self):
        """Check which audio library is available."""
        try:
            import sounddevice
            import scipy.io.wavfile
            return True
        except ImportError:
            return False

    def start(self):
        """Start recording in background thread."""
        self.is_recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        print(f"  [Audio]: Recording started (chunks every {self.chunk_duration//60} min)")

    def stop(self):
        """Stop recording and wait for thread to finish."""
        self.is_recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print(f"  [Audio]: Stopped. {self._chunk_count} chunks saved.")

    def get_chunk_count(self):
        return self._chunk_count

    def _record_loop(self):
        if self._use_sounddevice:
            self._record_with_sounddevice()
        else:
            self._record_with_pyaudio()

    # -----------------------------------------------
    # Method 1: sounddevice (preferred for laptops)
    # -----------------------------------------------
    def _record_with_sounddevice(self):
        import sounddevice as sd
        import numpy as np

        print("  [Audio]: Using sounddevice backend")
        frames_per_chunk = SAMPLE_RATE * self.chunk_duration

        while self.is_recording:
            self._chunk_count += 1
            filename = f"chunk_{self._chunk_count:03d}.wav"
            filepath = os.path.join(self.audio_dir, filename)

            print(f"  [Audio]: Recording chunk {self._chunk_count} → {filename}")

            try:
                # Record the full chunk duration
                recording = sd.rec(
                    frames_per_chunk,
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    blocking=False
                )

                # Wait while recording, checking is_recording flag every second
                for _ in range(self.chunk_duration):
                    if not self.is_recording:
                        sd.stop()
                        break
                    time.sleep(1)

                sd.wait()  # Ensure recording finishes

                # Save as WAV
                self._save_wav_numpy(filepath, recording)
                print(f"  [Audio]: Saved {filepath}")

            except Exception as e:
                print(f"  [Audio Error]: {e}")
                time.sleep(2)

    def _save_wav_numpy(self, filepath, data):
        """Save numpy array as WAV file."""
        import numpy as np
        import scipy.io.wavfile as wavfile
        # Flatten to 1D if needed
        if data.ndim > 1:
            data = data[:, 0]
        wavfile.write(filepath, SAMPLE_RATE, data.astype('int16'))

    # -----------------------------------------------
    # Method 2: pyaudio (fallback)
    # -----------------------------------------------
    def _record_with_pyaudio(self):
        try:
            import pyaudio
        except ImportError:
            print("  [Audio Error]: Neither sounddevice nor pyaudio found.")
            print("  Run: pip install sounddevice scipy")
            self.is_recording = False
            return

        print("  [Audio]: Using pyaudio backend")
        CHUNK = 1024
        p = pyaudio.PyAudio()

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            while self.is_recording:
                self._chunk_count += 1
                filename = f"chunk_{self._chunk_count:03d}.wav"
                filepath = os.path.join(self.audio_dir, filename)

                print(f"  [Audio]: Recording chunk {self._chunk_count} → {filename}")
                frames = []
                total = int(SAMPLE_RATE / CHUNK * self.chunk_duration)

                for _ in range(total):
                    if not self.is_recording:
                        break
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(data)
                    except Exception:
                        break

                if frames:
                    self._save_wav_pyaudio(filepath, frames, p)
                    print(f"  [Audio]: Saved {filepath}")

        except Exception as e:
            print(f"  [Audio Error]: {e}")
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            p.terminate()

    def _save_wav_pyaudio(self, filepath, frames, p):
        import pyaudio
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(frames))
