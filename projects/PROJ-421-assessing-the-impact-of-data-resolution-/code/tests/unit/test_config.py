"""Unit tests for configuration in code/config.py."""
import pytest
import config
from pathlib import Path

def test_config_resolutions():
    """Test that expected resolutions are defined."""
    assert hasattr(config, 'RESOLUTIONS')
    expected_resolutions = [30, 60, 120, 240, 480]
    assert config.RESOLUTIONS == expected_resolutions

def test_config_seeds():
    """Test that random seed is defined."""
    assert hasattr(config, 'RANDOM_SEED')
    assert config.RANDOM_SEED == 42

def test_config_paths_exist():
    """Test that base paths are defined and are Path objects."""
    assert hasattr(config, 'PROJECT_ROOT')
    assert isinstance(config.PROJECT_ROOT, Path)

    assert hasattr(config, 'DATA_RAW_DIR')
    assert isinstance(config.DATA_RAW_DIR, Path)

    assert hasattr(config, 'DATA_DERIVED_DIR')
    assert isinstance(config.DATA_DERIVED_DIR, Path)

    assert hasattr(config, 'DATA_RESULTS_DIR')
    assert isinstance(config.DATA_RESULTS_DIR, Path)

def test_config_huggingface_url():
    """Test that the HuggingFace URL is defined."""
    assert hasattr(config, 'NLCD_HF_URL')
    assert isinstance(config.NLCD_HF_URL, str)
    assert len(config.NLCD_HF_URL) > 0
