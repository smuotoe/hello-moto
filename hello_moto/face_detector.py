"""Face detection using MediaPipe Face Detection."""


class FaceDetector:
    """Detects faces using Google MediaPipe Face Detection.

    Returns True if a face with confidence >= min_detection_confidence is found.
    Uses model_selection=0 (short-range, best for faces <2m from camera).
    """

    def __init__(self, min_detection_confidence: float = 0.5) -> None:
        import mediapipe as mp

        self._detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=min_detection_confidence,
        )

    def _run_mediapipe(self, rgb_frame):
        """Run MediaPipe on an RGB frame (patchable for testing)."""
        return self._detector.process(rgb_frame)

    def detect(self, frame):
        """Detect a face in a BGR frame from the camera.

        Args:
            frame: BGR image from mini.media.get_frame() (or None if corrupt).

        Returns:
            (has_face, face_center_or_None). Face center is (x, y) in pixels.
        """
        # Guard against corrupt or missing frames
        if frame is None or frame.size == 0:
            return False, None

        # MediaPipe requires RGB input
        import cv2

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._run_mediapipe(rgb)

        if not results or not results.detections:
            return False, None

        # Return the first detected face (highest confidence)
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        h, w = frame.shape[:2]
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        cw = int(bbox.width * w)
        ch = int(bbox.height * h)
        center = (x + cw // 2, y + ch // 2)
        return True, center