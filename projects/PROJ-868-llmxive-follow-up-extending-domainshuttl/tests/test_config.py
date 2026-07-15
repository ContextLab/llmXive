"""Tests for configuration management."""
import pytest
from src.config import get_settings, Settings
from pathlib import Path


def test_settings_creation():
    """Test that settings object is created correctly."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.seed == 42
    assert settings.fidelity_threshold == 0.85
    assert 0.0 <= settings.fidelity_threshold <= 1.0


def test_settings_default_paths():
    """Test that default paths are relative to project root."""
    settings = get_settings()
    assert settings.data_root == Path("data")
    assert settings.src_root == Path("src")
    assert settings.tests_root == Path("tests")


def test_fidelity_threshold_validation():
    """Test that invalid fidelity threshold raises error."""
    with pytest.raises(ValueError):
        Settings(fidelity_threshold=1.5)
    
    with pytest.raises(ValueError):
        Settings(fidelity_threshold=-0.1)


def test_ensure_dirs():
    """Test that ensure_dirs creates necessary folders."""
    settings = get_settings()
    # This should not raise
    settings.ensure_dirs()
    assert settings.data_raw.exists()
