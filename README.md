# Hello Moto Reachy Mini

A script for your Reachy Mini (battery version) that plays the classic **"Hello Moto"** startup sound whenever it detects a person in front of it.

## How it works

1. Grabs frames from the Reachy Mini camera
2. Runs **MediaPipe face detection** (fast, runs on the onboard CPU)
3. When a face is consistently detected for ≥5 frames, plays the Hello Moto audio through the speaker
4. 5-second cooldown between greetings to avoid spam

## Setup

### 1. Install dependencies on the Reachy Mini

```bash
ssh reachy-mini
uv tool install reachy-mini mediapipe soundfile scipy
```

### 2. Get the Hello Moto sound file

Download the Hello Moto startup sound and save it as `hello-moto.wav`:

- **Myinstants** (play & download): https://www.myinstants.com/en/instant/hello-moto-highest-quality-38820/
- **Motorola-fans** (original ringtones): https://www.motorola-fans.com/2017/03/hellomoto-ringtone-2017-edit.html

Convert to WAV if needed:

```bash
ffmpeg -i hello-moto.mp3 hello-moto.wav
```

### 3. Copy files to the Reachy Mini

```bash
scp main.py hello-moto.wav reachy-mini:~/hello-moto/
```

### 4. Run

```bash
ssh reachy-mini
cd ~/hello-moto
python3 main.py
```

## Customization

Edit `main.py` to tweak:

| Setting             | Default | Description                                    |
| ------------------- | ------- | ---------------------------------------------- |
| `COOLDOWN_SECONDS`  | 5.0     | Gap between greetings                          |
| `FACE_THRESHOLD`    | 5       | Consecutive detection frames before triggering |
| `HEAD_TILT_DEGREES` | 5       | How much to tilt toward detected face          |
