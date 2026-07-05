"""
Tests for configuration management.
"""
import pytest
import os

from config import (
    RE_LAMBDA_VALUES,
    MAX_RSS_GB,
    VORTICITY_THRESHOLD_MULTIPLIERS,
    PROJECT_ROOT,
    DATA_DIR
)

def test_re_lambda_values():
    """Test that Reynolds number values are defined."""
    assert isinstance(RE_LAMBDA_VALUES, list)
    assert len(RE_LAMBDA_VALUES) > 0
    assert all(isinstance(r, int) for r in RE_LAMBDA_VALUES)

def test_memory_limit():
    """Test that memory limit is defined and positive."""
    assert MAX_RSS_GB > 0
    assert MAX_RSS_GB >= 1.0  # At least 1GB

def test_vorticity_thresholds():
    """Test that vorticity thresholds are defined."""
    assert isinstance(VORTICITY_THRESHOLD_MULTIPLIERS, list)
    assert len(VORTICITY_THRESHOLD_MULTIPLIERS) > 0
    assert all(isinstance(t, (int, float)) for t in VORTICITY_THRESHOLD_MULTIPLIERS)

def test_project_directories():
    """Test that required directories are defined."""
    assert os.path.isdir(PROJECT_ROOT) or os.path.exists(PROJECT_ROOT)
    assert os.path.isdir(DATA_DIR) or os.path.exists(DATA_DIR)

def test_config_imports():
    """Test that config module can be imported without errors."""
    try:
        import config
        assert hasattr(config, 'RE_LAMBDA_VALUES')
        assert hasattr(config, 'MAX_RSS_GB')
    except ImportError as e:
        pytest.fail(f"Failed to import config: {e}")