"""Tests for GreetingController."""

import pytest

from hello_moto.greeting_controller import GreetingController


@pytest.fixture
def controller():
    return GreetingController()


def test_requires_five_consecutive_frames(controller):
    """Five consecutive face detections should trigger a greeting."""
    triggered = False

    def on_greet():
        nonlocal triggered
        triggered = True

    controller.set_on_greet(on_greet)

    # 4 frames — should NOT trigger
    for _ in range(4):
        controller.update(has_face=True)
    assert triggered is False

    # 5th frame — SHOULD trigger
    controller.update(has_face=True)
    assert triggered is True


def test_counter_resets_on_face_loss(controller):
    """Counter resets to 0 when face disappears mid-sequence."""
    triggered = False

    def on_greet():
        nonlocal triggered
        triggered = True

    controller.set_on_greet(on_greet)

    for _ in range(3):
        controller.update(has_face=True)
    controller.update(has_face=False)
    for _ in range(4):
        controller.update(has_face=True)
    assert triggered is False

    controller.update(has_face=True)
    assert triggered is True


def test_cooldown_blocks_during_period(controller, monkeypatch):
    """During cooldown, face detections are ignored until timer expires."""
    triggered_count = 0

    def on_greet():
        nonlocal triggered_count
        triggered_count += 1

    controller.set_on_greet(on_greet)

    # Trigger one greeting
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 1
    assert controller._state == "playing"

    # End playback manually — enter cooldown
    controller.finish_playback()
    assert controller._state == "cooldown"

    # Faces during cooldown should NOT trigger (cooldown not expired yet)
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 1  # Still only one


def test_cooldown_expires(controller, monkeypatch):
    """After cooldown period, detection resumes from fresh."""
    triggered_count = 0

    def on_greet():
        nonlocal triggered_count
        triggered_count += 1

    controller.set_on_greet(on_greet)

    # Trigger one greeting
    for _ in range(5):
        controller.update(has_face=True)
    controller.finish_playback()

    # Fake time: cooldown expired
    monkeypatch.setattr(
        "hello_moto.greeting_controller.time.time",
        lambda: controller._cooldown_start + 3.0,
    )

    # Now 5 faces should trigger again
    for _ in range(5):
        controller.update(has_face=True)
    assert triggered_count == 2
