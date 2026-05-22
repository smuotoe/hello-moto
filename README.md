# Hello Moto

A Reachy Mini app that plays the classic "Hello Moto" startup sound when it detects a face.

Runs on the Wireless CM4 using OpenCV Haar cascade face detection.

## Installation

Install from the Reachy Mini dashboard with one click.

## How it works

1. The app continuously monitors the camera feed at ~10 fps
2. When a face is detected for 5 consecutive frames, it plays the Hello Moto sound
3. The controller owns the playback lifecycle — detection pauses during playback (~6.7s) and a 2s cooldown follows
4. After cooldown, it can greet again

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run python -m pytest tests/ -v
```

## Distribution

Published as a `reachy_mini_python_app` — discoverable in the Reachy Mini dashboard.
