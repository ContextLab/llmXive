"""
Tests for the environment configuration module (env_config).

These tests verify that CPU-only execution is properly enforced.
"""

import os
import sys
import pytest

# Test that the module can be imported without errors
def test_env_config_imports():
    """Test that env_config module can be imported."""
    from src.utils import env_config
    assert env_config is not None
    assert hasattr(env_config, 'enforce_cpu_only')
    assert hasattr(env_config, 'is_cpu_only_mode')
    assert hasattr(env_config, 'log_environment_config')

def test_enforce_cpu_only_sets_env_variable():
    """Test that enforce_cpu_only sets CUDA_VISIBLE_DEVICES to empty string."""
    from src.utils.env_config import enforce_cpu_only

    # Save original value
    original = os.environ.get("CUDA_VISIBLE_DEVICES")

    try:
        # Set to a non-empty value
        os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

        # Call the function
        result = enforce_cpu_only()

        # Verify it returned True
        assert result is True

        # Verify environment variable is now empty
        assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    finally:
        # Restore original value
        if original is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original

def test_is_cpu_only_mode_returns_true_when_empty():
    """Test is_cpu_only_mode returns True when CUDA_VISIBLE_DEVICES is empty."""
    from src.utils.env_config import is_cpu_only_mode

    # Save original value
    original = os.environ.get("CUDA_VISIBLE_DEVICES")

    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        assert is_cpu_only_mode() is True
    finally:
        if original is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original

def test_is_cpu_only_mode_returns_false_when_set():
    """Test is_cpu_only_mode returns False when CUDA_VISIBLE_DEVICES is set."""
    from src.utils.env_config import is_cpu_only_mode

    # Save original value
    original = os.environ.get("CUDA_VISIBLE_DEVICES")

    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        assert is_cpu_only_mode() is False
    finally:
        if original is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original

def test_module_load_enforces_cpu():
    """Test that importing the module enforces CPU-only mode."""
    # Save original value
    original = os.environ.get("CUDA_VISIBLE_DEVICES")

    try:
        # Set to a non-empty value before import
        os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

        # Re-import the module to trigger the top-level code
        if 'src.utils.env_config' in sys.modules:
            del sys.modules['src.utils.env_config']

        from src.utils import env_config

        # Verify environment variable is now empty
        assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    finally:
        if original is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original
