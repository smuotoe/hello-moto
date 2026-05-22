"""Controls greeting logic: consecutive face threshold + cooldown."""

import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger("reachy_mini.app")

FACE_THRESHOLD = 5
COOLDOWN_SECONDS = 2.0
DEFAULT_SOUND_DURATION = 6.7


class GreetingController:
    """Tracks consecutive face detections and triggers a greeting.

    - Requires FACE_THRESHOLD (5) consecutive face frames before triggering.
    - Resets counter on any non-face frame.
    - Resets counter on greeting trigger (after sound plays).
    - Pauses detection during playback.
    - Enforces a COOLDOWN_SECONDS pause after playback finishes.
    - Owns the playback timer internally (daemon thread).
    """

    def __init__(self, sound_duration: float = DEFAULT_SOUND_DURATION) -> None:
        self._consecutive = 0
        self._state = "idle"  # "idle" | "playing" | "cooldown"
        self._on_greet: Callable[[], None] = lambda: None
        self._cooldown_start = 0.0
        self._sound_duration = sound_duration

    def set_on_greet(self, callback: Callable[[], None]) -> None:
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

    def finish_playback(self) -> None:
        """Mark that sound playback has finished. Enters cooldown."""
        self._state = "cooldown"
        self._cooldown_start = time.time()
        logger.info(f"Cooldown started ({COOLDOWN_SECONDS}s)")

    def _trigger_greeting(self) -> None:
        """Fire the greeting callback, enter playback state, schedule cooldown."""
        self._state = "playing"
        self._consecutive = 0
        self._on_greet()
        # Schedule cooldown after sound finishes (daemon to not block shutdown)
        timer = threading.Timer(self._sound_duration, self.finish_playback)
        timer.daemon = True
        timer.start()
