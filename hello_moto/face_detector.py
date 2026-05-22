"""Face detection using OpenCV Haar cascade."""

from pathlib import Path

import cv2
import cv2.data


class FaceDetector:
    """Detects faces using the default OpenCV Haar cascade.

    Returns True if a face with bounding box >= 20x20 pixels is found.
    """

    def __init__(self) -> None:
        cascade_path = str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
        self._cascade = cv2.CascadeClassifier(cascade_path)
        if self._cascade.empty():
            raise RuntimeError(f"Failed to load Haar cascade from {cascade_path}")

    def _run_cascade(self, gray):
        """Run the cascade on a grayscale frame (patchable for testing)."""
        return self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    def detect(self, frame):
        """Detect a face in a BGR frame from the camera.

        Args:
            frame: BGR image from mini.media.get_frame() (or None if corrupt).

        Returns:
            (has_face, face_center_or_None). Face center is (x, y) in pixels.
            Bounding box must be >= 20x20 to count.
        """
        # Guard against corrupt or missing frames
        if frame is None or frame.size == 0:
            return False, None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._run_cascade(gray)

        # Filter: bounding box must be >= 20x20
        valid = [(x, y, w, h) for x, y, w, h in faces if w >= 20 and h >= 20]
        if not valid:
            return False, None

        # Return the largest detected face
        best = max(valid, key=lambda r: r[2] * r[3])
        x, y, w, h = best
        center = (x + w // 2, y + h // 2)
        return True, center