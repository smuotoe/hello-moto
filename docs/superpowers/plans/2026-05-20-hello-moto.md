# Hello Moto App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Reachy Mini Python app that plays "Hello Moto" when it detects a face, packaged for Hugging Face distribution.

**Architecture:** Restructure existing `main.py` into a proper `ReachyMiniApp` subclass with `FaceDetector` (OpenCV Haar cascade) and `GreetingController` (consecutive-frame threshold + cooldown) as focused components. Uses `mini.media.play_sound()` instead of manual sample pushing.

**Tech Stack:** `reachy-mini` SDK, `opencv-python-headless`, Python `logging`

---

### Task 1: Set up package structure

**Files:**

- Create: `pyproject.toml`
- Create: `hello_moto/__init__.py`
- Create: `hello_moto/main.py` (new, from scratch — the old `main.py` root script is replaced)
- Create: `hello_moto/assets/`
- Move: `hello-moto.wav` → `hello_moto/assets/hello-moto.wav`
- Modify: `requirements.txt` (replace mediapipe/soundfile/scipy with opencv-python-headless)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p hello_moto/assets tests
mv hello-moto.wav hello_moto/assets/hello-moto.wav
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "hello-moto"
version = "0.1.0"
description = "Plays Hello Moto sound when a face is detected"
requires-python = ">=3.10"
dependencies = [
    "reachy-mini",
    "opencv-python-headless",
]

[project.entry-points."reachy_mini_apps"]
hello_moto = "hello_moto.main:HelloMotoApp"

[tool.setuptools.packages.find]
include = ["hello_moto*"]

[tool.setuptools.package-data]
hello_moto = ["assets/*.wav"]
```

- [ ] **Step 3: Write `hello_moto/__init__.py`**

```python
"""Hello Moto — Reachy Mini face-greeting app."""
```

- [ ] **Step 4: Write `hello_moto/main.py` scaffold**

```python
"""Reachy Mini app that plays Hello Moto on face detection."""

import logging
import threading
from pathlib import Path

import cv2

from reachy_mini import ReachyMini
from reachy_mini.apps import ReachyMiniApp


logger = logging.getLogger("reachy_mini.app")


class HelloMotoApp(ReachyMiniApp):
    """Says Hello Moto when it sees a face."""

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        logger.info("Hello Moto app starting...")
```

- [ ] **Step 5: Update `requirements.txt`**

```
reachy-mini
opencv-python-headless
```

- [ ] **Step 6: Run basic import verification**

```bash
cd /home/megamind/projects/hello-moto
python -c "from hello_moto.main import HelloMotoApp; print('OK')"
```

Expected: `OK` (or import error for `reachy-mini`/`cv2` if not installed locally — that's fine, the code structure is correct)

- [ ] **Step 7: Commit**

```bash
rm main.py
git init
git add .
git commit -m "feat: set up package structure with ReachyMiniApp scaffold"
```

---

### Task 2: Implement FaceDetector

**Files:**

- Create: `hello_moto/face_detector.py`
- Create: `tests/test_face_detector.py`

- [ ] **Step 1: Write the failing test — no face detected**

```python
"""Tests for FaceDetector."""

import cv2
import numpy as np
import pytest

from hello_moto.face_detector import FaceDetector


@pytest.fixture
def detector():
    return FaceDetector()


def test_no_face_returns_false(detector):
    # 640x480 grayscale frame with no face
    frame = np.zeros((480, 640), dtype=np.uint8)
    has_face, center = detector.detect(frame)
    assert has_face is False
    assert center is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/megamind/projects/hello-moto
python -m pytest tests/test_face_detector.py::test_no_face_returns_false -v
```

Expected: `ImportError` or `ModuleNotFoundError` for `hello_moto.face_detector`

- [ ] **Step 3: Write `hello_moto/face_detector.py`**

```python
"""Face detection using OpenCV Haar cascade."""

import logging
from pathlib import Path

import cv2
import cv2.data

logger = logging.getLogger("reachy_mini.app")


class FaceDetector:
    """Detects faces using the default OpenCV Haar cascade.

    Returns True if a face with bounding box >= 20x20 pixels is found.
    """

    def __init__(self) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier()
        if self._cascade.read(str(cascade_path)) is False:
            raise RuntimeError(f"Failed to load Haar cascade from {cascade_path}")

    def detect(self, frame: "np.ndarray") -> tuple[bool, tuple[int, int] | None]:
        """Detect a face in a BGR frame from the camera.

        Args:
            frame: BGR image from mini.media.get_frame().

        Returns:
            (has_face, face_center_or_None). Face center is (x, y) in pixels.
            Bounding box must be >= 20x20 to count.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        # Filter: bounding box must be >= 20x20
        valid = [(x, y, w, h) for x, y, w, h in faces if w >= 20 and h >= 20]
        if not valid:
            return False, None

        # Return the largest detected face
        best = max(valid, key=lambda r: r[2] * r[3])
        x, y, w, h = best
        center = (x + w // 2, y + h // 2)
        return True, center
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_face_detector.py::test_no_face_returns_false -v
```

Expected: `PASS`

- [ ] **Step 5: Add test — face detected with valid size**

Append to `tests/test_face_detector.py`:

```python
def test_face_detected_large_enough(monkeypatch, detector):
    # Simulate a 200x200 face in a 640x480 frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Patch detectMultiScale to return a face
    mock_faces = np.array([[200, 100, 200, 200]], dtype=np.int32)
    monkeypatch.setattr(detector._cascade, "detectMultiScale", lambda *a, **k: mock_faces)

    has_face, center = detector.detect(frame)
    assert has_face is True
    assert center == (300, 200)
```

- [ ] **Step 6: Add test — face too small is ignored**

```python
def test_face_too_small_ignored(monkeypatch, detector):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_faces = np.array([[100, 100, 10, 10]], dtype=np.int32)
    monkeypatch.setattr(detector._cascade, "detectMultiScale", lambda *a, **k: mock_faces)

    has_face, center = detector.detect(frame)
    assert has_face is False
    assert center is None
```

- [ ] **Step 7: Run all face detector tests**

```bash
python -m pytest tests/test_face_detector.py -v
```

Expected: `3 passed`

- [ ] **Step 8: Commit**

```bash
git add hello_moto/face_detector.py tests/test_face_detector.py
git commit -m "feat: implement FaceDetector with Haar cascade and size filter"
```

---

### Task 3: Implement GreetingController

**Files:**

- Create: `hello_moto/greeting_controller.py`
- Create: `tests/test_greeting_controller.py`

- [ ] **Step 1: Write the failing test — needs 5 consecutive frames**

```python
"""Tests for GreetingController."""

import pytest

from hello_moto.greeting_controller import GreetingController


@pytest.fixture
def controller():
    return GreetingController()


def test_requires_five_consecutive_frames(controller):
    """Five consecutive face detections should trigger a greeting."""
    triggered = False

    def on_greet():
        nonlocal triggered
        triggered = True

    controller.set_on_greet(on_greet)

    # 4 frames — should NOT trigger
    for _ in range(4):
        controller.update(has_face=True)
    assert triggered is False

    # 5th frame — SHOULD trigger
    controller.update(has_face=True)
    assert triggered is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_greeting_controller.py::test_requires_five_consecutive_frames -v
```

Expected: `ModuleNotFoundError` for `hello_moto.greeting_controller`

- [ ] **Step 3: Write `hello_moto/greeting_controller.py`**

```python
"""Controls greeting logic: consecutive face threshold + cooldown."""

import logging
import time

logger = logging.getLogger("reachy_mini.app")

FACE_THRESHOLD = 5
COOLDOWN_SECONDS = 2.0


class GreetingController:
    """Tracks consecutive face detections and triggers a greeting.

    - Requires FACE_THRESHOLD (5) consecutive face frames before triggering.
    - Resets counter on any non-face frame.
    - Resets counter on greeting trigger (after sound plays).
    - Pauses detection during playback.
    - Enforces a COOLDOWN_SECONDS pause after playback finishes.
    """

    def __init__(self) -> None:
        self._consecutive = 0
        self._state = "idle"  # "idle" | "playing" | "cooldown"
        self._on_greet: callable = lambda: None
        self._cooldown_start = 0.0

    def set_on_greet(self, callback: callable) -> None:
        """Set the callback to invoke when a greeting should play."""
        self._on_greet = callback

    def update(self, has_face: bool) -> None:
        """Process one frame's face detection result.

        Call this each frame with the result from FaceDetector.
        If in playing/cooldown state, the result is ignored.
        """
        if self._state == "playing":
            return

        if self._state == "cooldown":
            if time.time() - self._cooldown_start >= COOLDOWN_SECONDS:
                logger.info("Cooldown ended, resuming detection")
                self._state = "idle"
                self._consecutive = 0
            else:
                return
            # Fall through to process the current frame as idle

        if has_face:
            self._consecutive += 1
            if self._consecutive >= FACE_THRESHOLD:
                logger.info(f"Face confirmed ({self._consecutive} frames), greeting!")
                self._trigger_greeting()
        else:
            if self._consecutive > 0:
                logger.info(f"Face lost at frame {self._consecutive}, resetting")
            self._consecutive = 0

    def start_playback(self) -> None:
        """Mark that sound playback has started. Pauses detection."""
        self._state = "playing"
        self._consecutive = 0

    def finish_playback(self) -> None:
        """Mark that sound playback has finished. Enters cooldown."""
        self._state = "cooldown"
        self._cooldown_start = time.time()
        logger.info(f"Cooldown started ({COOLDOWN_SECONDS}s)")

    def _trigger_greeting(self) -> None:
        """Fire the greeting callback and enter playback state."""
        self._state = "playing"
        self._consecutive = 0
        self._on_greet()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_greeting_controller.py::test_requires_five_consecutive_frames -v
```

Expected: `PASS`

- [ ] **Step 5: Add test — counter resets on face loss**

Append to `tests/test_greeting_controller.py`:

```python
def test_counter_resets_on_face_loss(controller):
    """Counter resets to 0 when face disappears mid-sequence."""
    triggered = False
    def on_greet():
        nonlocal triggered
        triggered = True
    controller.set_on_greet(on_greet)

    for _ in range(3):
        controller.update(has_face=True)
    controller.update(has_face=False)
    for _ in range(4):
        controller.update(has_face=True)
    assert triggered is False

    controller.update(has_face=True)
    assert triggered is True
```

- [ ] **Step 6: Add test — cooldown prevents immediate re-trigger**

```python
def test_cooldown_blocks_during_period(controller, monkeypatch):
    """During cooldown, face detections are ignored until timer expires."""
    triggered_count = 0
    def on_greet():
        nonlocal triggered_count
        triggered_count += 1
    controller.set_on_greet(on_greet)

    # Trigger one greeting
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 1
    assert controller._state == "playing"

    # End playback — enter cooldown
    controller.finish_playback()
    assert controller._state == "cooldown"

    # Faces during cooldown should NOT trigger (cooldown not expired yet)
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 1  # Still only one
```

- [ ] **Step 7: Add test — cooldown expiry resumes detection**

```python
def test_cooldown_expires(controller, monkeypatch):
    """After cooldown period, detection resumes from fresh."""
    triggered_count = 0
    def on_greet():
        nonlocal triggered_count
        triggered_count += 1
    controller.set_on_greet(on_greet)

    # Trigger one greeting
    for _ in range(5):
        controller.update(has_face=True)
    controller.finish_playback()

    # Fake time: cooldown expired
    monkeypatch.setattr("hello_moto.greeting_controller.time.time", lambda: controller._cooldown_start + 3.0)

    # Now 5 faces should trigger again
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 2
```

- [ ] **Step 8: Run all controller tests**

```bash
python -m pytest tests/test_greeting_controller.py -v
```

Expected: `4 passed`

- [ ] **Step 9: Commit**

```bash
git add hello_moto/greeting_controller.py tests/test_greeting_controller.py
git commit -m "feat: implement GreetingController with threshold, cooldown, playback states"
```

---

### Task 4: Wire up HelloMotoApp main loop

**Files:**

- Modify: `hello_moto/main.py`
- Create: `tests/test_hello_moto_app.py`

- [ ] **Step 1: Write the failing integration test — asset path resolution**

```python
"""Tests for HelloMotoApp asset resolution."""

import pytest
from pathlib import Path

from hello_moto.main import HelloMotoApp


def test_sound_path_resolves():
    """The app should find its bundled WAV file."""
    app = HelloMotoApp()
    sound_path = app._get_sound_path()
    assert sound_path.exists(), f"Sound file not found: {sound_path}"
    assert sound_path.suffix == ".wav"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_hello_moto_app.py::test_sound_path_resolves -v
```

Expected: `AttributeError: '_HelloMotoApp' object has no attribute '_get_sound_path'`

- [ ] **Step 3: Write the complete `hello_moto/main.py`**

```python
"""Reachy Mini app that plays Hello Moto on face detection."""

import logging
import threading
from pathlib import Path

from reachy_mini import ReachyMini
from reachy_mini.apps import ReachyMiniApp

from hello_moto.face_detector import FaceDetector
from hello_moto.greeting_controller import GreetingController

logger = logging.getLogger("reachy_mini.app")

# Duration of the Hello Moto sound in seconds
SOUND_DURATION = 6.7


class HelloMotoApp(ReachyMiniApp):
    """Says Hello Moto when it sees a face."""

    def _get_sound_path(self) -> Path:
        """Resolve the bundled WAV file to an absolute path."""
        base = Path(__file__).resolve().parent
        sound = base / "assets" / "hello-moto.wav"
        return sound.resolve()

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        logger.info("Hello Moto app starting...")

        # Load face detector (fails fast if cascade unavailable)
        detector = FaceDetector()
        logger.info("Face detector initialized")

        # Resolve sound path
        sound_path = self._get_sound_path()
        if not sound_path.exists():
            self.error = f"Sound file not found: {sound_path}"
            logger.error(self.error)
            raise RuntimeError(self.error)
        logger.info(f"Sound file ready: {sound_path}")

        controller = GreetingController()

        def on_greet():
            logger.info("Playing Hello Moto...")
            controller.start_playback()
            try:
                reachy_mini.media.play_sound(str(sound_path))
                # play_sound is non-blocking; wait for duration
                threading.Timer(SOUND_DURATION, controller.finish_playback).start()
            except Exception:
                logger.warning(f"play_sound failed: {self.error}")
                controller.finish_playback()  # Reset state on failure

        controller.set_on_greet(on_greet)

        # Main detection loop (~10 fps)
        while not stop_event.is_set():
            try:
                frame = reachy_mini.media.get_frame()
                if frame is None:
                    logger.warning("get_frame returned None")
                    has_face = False
                else:
                    has_face, center = detector.detect(frame)
                    if has_face and center:
                        logger.info(f"Face detected at {center}")
            except Exception as e:
                logger.warning(f"Frame detection error: {e}")
                has_face = False

            controller.update(has_face)
            stop_event.wait(0.3)  # ~10 fps

        logger.info("Hello Moto app stopped.")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_hello_moto_app.py::test_sound_path_resolves -v
```

Expected: `PASS` (assuming WAV was moved to `hello_moto/assets/`)

- [ ] **Step 5: Add test — app structure has required attributes**

Append to `tests/test_hello_moto_app.py`:

```python
def test_app_has_required_methods():
    """Verify the app implements the ReachyMiniApp interface."""
    app = HelloMotoApp()
    assert hasattr(app, 'run')
    assert hasattr(app, 'stop')
    assert hasattr(app, 'stop_event')
    assert hasattr(app, '_get_sound_path')
```

- [ ] **Step 6: Run all app tests**

```bash
python -m pytest tests/test_hello_moto_app.py -v
```

Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add hello_moto/main.py tests/test_hello_moto_app.py
git commit -m "feat: wire up HelloMotoApp with face detection loop and sound playback"
```

---

### Task 5: Write README.md for Hugging Face distribution

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Write the README with required frontmatter**

```markdown
---
title: Hello Moto
emoji: 👋
colorFrom: green
colorTo: yellow
sdk: python
pinned: false
short_description: Reachy Mini plays Hello Moto when it sees a face
tags:
  - reachy_mini
  - reachy_mini_python_app
---

# Hello Moto

A Reachy Mini app that plays the classic "Hello Moto" startup sound when it detects a face.

Runs on the Wireless CM4 using OpenCV Haar cascade face detection.

## Installation

Install from the Reachy Mini dashboard with one click.

## How it works

1. The app continuously monitors the camera feed at ~10 fps
2. When a face is detected for 5 consecutive frames, it plays the Hello Moto sound
3. After playing, it waits 2 seconds before it can greet again
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with reachy_mini_python_app tag for Hugging Face distribution"
```

---

### Task 6: Final verification

**Files:**

- All project files

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: `All tests pass` (7 tests: 2 face_detector, 4 greeting_controller, 2 hello_moto_app)

- [ ] **Step 2: Verify package structure**

```bash
find hello_moto -type f | sort
```

Expected output:

```
hello_moto/__init__.py
hello_moto/assets/hello-moto.wav
hello_moto/face_detector.py
hello_moto/greeting_controller.py
hello_moto/main.py
```

- [ ] **Step 3: Verify pyproject.toml entry point**

```bash
grep -A2 'entry-points' pyproject.toml
```

Expected: `hello_moto = "hello_moto.main:HelloMotoApp"`

- [ ] **Step 4: Verify package-data includes assets**

```bash
grep -A2 'package-data' pyproject.toml
```

Expected: `hello_moto = ["assets/*.wav"]`

- [ ] **Step 5: Commit**

```bash
git commit -am "chore: final verification pass"
```
