"""Tests for FaceDetector (MediaPipe-based)."""

import numpy as np
import pytest

from hello_moto.face_detector import FaceDetector


@pytest.fixture
def detector():
    return FaceDetector()


def test_no_face_returns_false(detector):
    """A blank frame should return no face."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    has_face, center = detector.detect(frame)
    assert has_face is False
    assert center is None


def test_none_frame_returns_false(detector):
    """A None frame should not crash detect() and return no face."""
    has_face, center = detector.detect(None)
    assert has_face is False
    assert center is None


def test_empty_frame_returns_false(detector):
    """An empty frame should return no face."""
    has_face, center = detector.detect(np.array([], dtype=np.uint8))
    assert has_face is False
    assert center is None


def test_mediapipe_detection_patched(monkeypatch, detector):
    """Simulate MediaPipe finding a face by patching _run_mediapipe."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    class MockBBox:
        xmin = 0.3
        ymin = 0.2
        width = 0.25
        height = 0.3

    class MockLocationData:
        relative_bounding_box = MockBBox()

    class MockDetection:
        location_data = MockLocationData()

    class MockResults:
        detections = [MockDetection()]

    monkeypatch.setattr(detector, "_run_mediapipe", lambda rgb: MockResults())

    has_face, center = detector.detect(frame)
    assert has_face is True
    # Center of bbox at relative (0.3+0.125, 0.2+0.15) * (640, 480)
    assert center == (272, 168)
