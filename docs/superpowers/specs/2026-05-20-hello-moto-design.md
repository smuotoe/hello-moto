# Hello Moto App — Design

## Overview

A Reachy Mini app that plays the classic "Hello Moto" startup sound when it detects a face in front of the robot. Runs entirely on the Wireless CM4.

## Architecture

**App type**: Python app using `ReachyMiniApp` base class, managed by the Reachy Mini daemon.

**Package structure**:

```
hello_moto/
├── pyproject.toml          # Entry point + opencv-python-headless dependency
├── README.md               # With reachy_mini_python_app tag
├── hello_moto/
│   ├── __init__.py
│   ├── main.py             # ReachyMiniApp subclass with run() loop
│   └── assets/
│       └── hello-moto.wav  # 6.7s Mono 16kHz PCM sound file
```

**Entry point**: `hello_moto.main:HelloMotoApp` registered via `pyproject.toml` under `[project.entry-points."reachy_mini_apps"]`.

## Components

### 1. FaceDetector

- Uses OpenCV Haar cascade (`haarcascade_frontalface_default.xml` bundled with `opencv-python`).
- Runs on each camera frame from `mini.media.get_frame()`, converted to grayscale.
- Filters detections: bounding box must be ≥20×20 pixels.
- Returns `(has_face: bool, face_center: tuple | None)`.

### 2. GreetingController

- Tracks consecutive face frames (threshold: 5).
- **Counter resets to 0 on ANY frame where no face is detected** — frames must be truly consecutive.
- **Counter resets to 0 on greeting trigger** — after `play_sound()` fires, the count starts fresh.
- Enforces a **2-second cooldown after playback finishes** before allowing detection to count again.
- Detection is **paused entirely during playback** (~6.7 seconds) to avoid double-trigger.
- Total dead time between greetings: ~8.7s (6.7s playback + 2s cooldown).
- Calls `mini.media.play_sound(assets_path)` when triggered.

### 3. Main Loop (`run()`)

- Runs at ~10 fps (300ms sleep between frames).
- Each iteration: grab frame → detect face → update controller → check `stop_event`.
- Polls `stop_event.is_set()` for graceful daemon-initiated shutdown.
- **Error handling:**
  - `get_frame()` failures: caught and treated as "no face" (counter resets). App keeps running.
  - `play_sound()` failures: caught and logged as a warning. App keeps running.
  - Haar cascade load failure: fails fast at startup with a clear log message.
- **Debug output:** Uses Python `logging` module (`info` for key events, `warning` for errors). Output goes to stdout for daemon capture.

## Data Flow

```
Camera → get_frame() → grayscale → Haar cascade → face detected?
  → GreetingController (consecutive count + cooldown logic)
    → play_sound(wav_path) → Reachy Mini speaker
```

## Platform

- **Target**: Reachy Mini Wireless (CM4, battery).
- **Media backend**: `default` (auto-detected by `ReachyMiniApp.wrapped_run()`).
- **Connection mode**: `localhost_only` (runs on same machine as daemon).

## Dependencies

- `reachy-mini` (SDK, pre-installed on CM4)
- `opencv-python-headless` (for Haar cascade; no X11 dependency)

## Asset Packaging

- `pyproject.toml` must include `[tool.setuptools.package-data]` to ship `assets/*.wav`:
  ```toml
  [tool.setuptools.package-data]
  hello_moto = ["assets/*.wav"]
  ```
- The WAV path is resolved to an absolute path at runtime (via `os.path.abspath()` or `importlib.resources`) before passing to `play_sound()`, which requires an absolute path on the local backend.

## Sound Format

- WAV file is standard PCM, Mono, 16kHz — matches the Reachy Mini's native audio sample rate.
- GStreamer `playbin` handles standard WAV files directly. No resampling needed.

## Distribution

- Published to Hugging Face Spaces as a public app.
- Discoverable via `reachy_mini_python_app` tag in README frontmatter.
- Installed from the Reachy Mini dashboard with one click.
