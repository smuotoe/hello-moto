# Hello Moto

A Reachy Mini app that plays the classic "Hello Moto" startup sound when it detects a face. Runs entirely on the Wireless CM4.

## Language

**GreetingController**:
A state machine managing the lifecycle of face-detection counting, sound playback, and cooldown. States: `idle`, `playing`, `cooldown`. Owns the playback timer internally.
_Avoid_: Trigger manager, state handler

**FaceDetector**:
An OpenCV Haar cascade wrapper that detects faces in BGR camera frames. Returns a `(has_face, face_center)` tuple. Defensively guards against `None`/empty frames.
_Avoid_: Face recognizer, detector

**Greeting**:
The act of playing the Hello Moto sound in response to confirmed face detection. A greeting fires once per detection sequence and is suppressed during playback and cooldown.

**Consecutive threshold**:
The number of uninterrupted face frames (5) required before a greeting is triggered. Zero tolerance — any non-face frame resets the counter. Not configurable.

**Playback**:
The period (~6.7 seconds, derived from WAV metadata at startup) during which the sound is actively playing. Detection is paused during playback.

**Cooldown**:
A 2-second post-playback window where detection resumes but new greetings are suppressed. Prevents re-triggering from the same face still being in frame.

**Face detection**:
Binary result from FaceDetector — a face was found in the current camera frame with a bounding box ≥ 20×20 pixels.

## Example dialogue

**Dev**: "I stood in front of the robot for 3 seconds and it only greeted me once."
**Domain expert**: "That's correct. It needs 5 consecutive frames (~500ms) to confirm you're a face, then it plays the greeting. During the 6.7s playback and the 2s cooldown, it ignores all faces. After that, if you're still there, it needs another 5 consecutive frames."
**Dev**: "So the total quiet period between greetings is roughly 8.7 seconds minimum?"
**Domain expert**: "Exactly. And if you look away for even one frame during those 500ms — counter resets to zero."