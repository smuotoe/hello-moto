"""Tests for GreetingController (single-frame trigger)."""

import pytest

from hello_moto.greeting_controller import GreetingController


@pytest.fixture
def controller():
    return GreetingController()


def test_single_frame_triggers_greeting(controller):
    """A single face detection should immediately trigger a greeting."""
    triggered = False

    def on_greet():
        nonlocal triggered
        triggered = True

    controller.set_on_greet(on_greet)
    controller.update(has_face=True)
    assert triggered is True


def test_no_face_does_not_trigger(controller):
    """No face detection should not trigger anything."""
    triggered = False

    def on_greet():
        nonlocal triggered
        triggered = True

    controller.set_on_greet(on_greet)
    controller.update(has_face=False)
    assert triggered is False


def test_playing_state_ignores_faces(controller):
    """During playback (playing state), face detections should be ignored."""
    triggered_count = 0

    def on_greet():
        nonlocal triggered_count
        triggered_count += 1

    controller.set_on_greet(on_greet)

    # First face triggers the greeting
    controller.update(has_face=True)
    assert triggered_count == 1
    assert controller._state == "playing"

    # Faces during playing should be ignored
    controller.update(has_face=True)
    controller.update(has_face=True)
    assert triggered_count == 1  # Still only one


def test_cooldown_blocks_during_period(controller):
    """During cooldown, face detections are ignored until timer expires."""
    triggered_count = 0

    def on_greet():
        nonlocal triggered_count
        triggered_count += 1

    controller.set_on_greet(on_greet)

    # Trigger one greeting
    controller.update(has_face=True)
    assert triggered_count == 1
    assert controller._state == "playing"

    # End playback manually — enter cooldown
    controller.finish_playback()
    assert controller._state == "cooldown"

    # Faces during cooldown should NOT trigger
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 1  # Still only one


def test_cooldown_expires(controller, monkeypatch):
    """After cooldown period, detection resumes."""
    triggered_count = 0

    def on_greet():
        nonlocal triggered_count
        triggered_count += 1

    controller.set_on_greet(on_greet)

    # Trigger one greeting
    controller.update(has_face=True)
    controller.finish_playback()

    # Fake time: cooldown expired
    monkeypatch.setattr(
        "hello_moto.greeting_controller.time.time",
        lambda: controller._cooldown_start + 3.0,
    )

    # First call: cooldown expired, resets state to idle without processing the frame
    controller.update(has_face=True)
    assert triggered_count == 1

    # Second call: state is idle, face is present → triggers a new greeting
    controller.update(has_face=True)
    assert triggered_count == 2
