"""Tests for HelloMotoApp."""

from hello_moto.main import HelloMotoApp


def test_sound_path_resolves():
    """The app should find its bundled WAV file."""
    app = HelloMotoApp()
    sound_path = app._get_sound_path()
    assert sound_path.exists(), f"Sound file not found: {sound_path}"
    assert sound_path.suffix == ".wav"


def test_sound_duration_reads():
    """The app should read WAV duration from file metadata."""
    app = HelloMotoApp()
    sound_path = app._get_sound_path()
    duration = HelloMotoApp._get_sound_duration(sound_path)
    assert isinstance(duration, float)
    assert duration > 0


def test_app_has_required_methods():
    """Verify the app implements the ReachyMiniApp interface."""
    app = HelloMotoApp()
    assert hasattr(app, "run")
    assert hasattr(app, "_get_sound_path")
