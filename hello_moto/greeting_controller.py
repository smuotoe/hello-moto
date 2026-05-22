"""Controls greeting logic: single-frame trigger + cooldown."""

import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger("reachy_mini.app")

COOLDOWN_SECONDS = 2.0
DEFAULT_SOUND_DURATION = 6.7


class GreetingController:
    """Triggers a greeting on any face detection, with cooldown.

    - Triggers immediately on any face detection (single frame).
    - Pauses detection during playback.
    - Enforces a COOLDOWN_SECONDS pause after playback finishes.
    - Owns the playback timer internally (daemon thread).
    """

    def __init__(self, sound_duration: float = DEFAULT_SOUND_DURATION) -> None:
        self._state = "idle"  # "idle" | "playing" | "cooldown"
        self._on_greet: Callable[[], None] = lambda: None
        self._cooldown_start = 0.0
        self._sound_duration = sound_duration
        self._triggering = False  # re-entrancy guard

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
                return  # Don't process this frame, wait for next one
            else:
                return

        if has_face:
            logger.info("Face detected, greeting!")
            self._trigger_greeting()

    def finish_playback(self) -> None:
        """Mark that sound playback has finished. Enters cooldown."""
        self._state = "cooldown"
        self._cooldown_start = time.time()
        logger.info(f"Cooldown started ({COOLDOWN_SECONDS}s)")

    def _trigger_greeting(self) -> None:
        """Fire the greeting callback, enter playback state, schedule cooldown."""
        if self._triggering:
            return  # Already in the process of triggering
        self._triggering = True
        try:
            if self._state == "playing":
                return  # Guard against double-fire
            self._state = "playing"
            self._on_greet()
            # Schedule cooldown after sound finishes (daemon to not block shutdown)
            timer = threading.Timer(self._sound_duration, self.finish_playback)
            timer.daemon = True
            timer.start()
        finally:
            self._triggering = False
