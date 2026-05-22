"""Tests for FaceDetector."""

import cv2
import numpy as np
import pytest

from hello_moto.face_detector import FaceDetector


@pytest.fixture
def detector():
    return FaceDetector()


def test_no_face_returns_false(detector):
    # 640x480 BGR frame with no face
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    has_face, center = detector.detect(frame)
    assert has_face is False
    assert center is None


def test_none_frame_returns_false(detector):
    """A None frame should not crash detect() and return no face."""
    has_face, center = detector.detect(None)
    assert has_face is False
    assert center is None


def test_face_detected_large_enough(monkeypatch, detector):
    # Simulate a 200x200 face in a 640x480 frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Patch _run_cascade to return a face
    mock_faces = np.array([[200, 100, 200, 200]], dtype=np.int32)
    monkeypatch.setattr(detector, "_run_cascade", lambda gray: mock_faces)

    has_face, center = detector.detect(frame)
    assert has_face is True
    assert center == (300, 200)


def test_face_too_small_ignored(monkeypatch, detector):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_faces = np.array([[100, 100, 10, 10]], dtype=np.int32)
    monkeypatch.setattr(detector, "_run_cascade", lambda gray: mock_faces)

    has_face, center = detector.detect(frame)
    assert has_face is False
    assert center is None
