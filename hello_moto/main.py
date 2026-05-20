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
