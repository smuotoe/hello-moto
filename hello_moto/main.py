"""Reachy Mini app that plays Hello Moto on face detection."""

import logging
import threading
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from hello_moto.face_detector import FaceDetector
from hello_moto.greeting_controller import GreetingController

if TYPE_CHECKING:
    from reachy_mini import ReachyMini

logger = logging.getLogger("reachy_mini.app")


class HelloMotoApp:
    """Says Hello Moto when it sees a face."""

    def _get_sound_path(self) -> Path:
        """Resolve the bundled WAV file to an absolute path."""
        base = Path(__file__).resolve().parent
        sound = base / "assets" / "hello-moto.wav"
        return sound.resolve()

    @staticmethod
    def _get_sound_duration(path: Path) -> float:
        """Read the duration of a WAV file in seconds using stdlib wave module."""
        with wave.open(str(path), "r") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
        return frames / rate if rate > 0 else 6.7

    def run(self, reachy_mini, stop_event: threading.Event) -> None:
        logger.info("Hello Moto app starting...")

        # Load face detector (fails fast if cascade unavailable)
        detector = FaceDetector()
        logger.info("Face detector initialized")

        # Resolve sound path and duration from WAV metadata
        sound_path = self._get_sound_path()
        if not sound_path.exists():
            self.error = f"Sound file not found: {sound_path}"
            logger.error(self.error)
            raise RuntimeError(self.error)
        sound_duration = self._get_sound_duration(sound_path)
        logger.info(f"Sound file ready: {sound_path} ({sound_duration:.1f}s)")

        # Controller owns the playback timer internally
        controller = GreetingController(sound_duration=sound_duration)

        def on_greet():
            logger.info("Playing Hello Moto...")
            try:
                reachy_mini.media.play_sound(str(sound_path))
                # Controller schedules its own finish_playback timer
            except Exception:
                logger.warning(f"play_sound failed: {sound_path}")
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
                        logger.debug(f"Face detected at {center}")
            except Exception as e:
                logger.warning(f"Frame detection error: {e}")
                has_face = False

            controller.update(has_face)
            stop_event.wait(0.3)  # ~10 fps

        logger.info("Hello Moto app stopped.")
