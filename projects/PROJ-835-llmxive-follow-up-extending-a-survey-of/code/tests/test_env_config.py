"""
Tests for environment configuration utilities.

These tests verify that the CPU-only enforcement mechanism works correctly.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import importlib

# Import the module to be tested
from src.utils.env_config import (
    enforce_cpu_only,
    is_cpu_only_mode,
    log_environment_config,
)

def test_env_config_imports():
    """Test that the env_config module can be imported without errors."""
    try:
        from src.utils import env_config
        assert hasattr(env_config, 'enforce_cpu_only')
        assert hasattr(env_config, 'is_cpu_only_mode')
        assert hasattr(env_config, 'log_environment_config')
    except ImportError as e:
        pytest.fail(f"Failed to import env_config module: {e}")

def test_enforce_cpu_only_sets_env_variable():
    """Test that enforce_cpu_only sets CUDA_VISIBLE_DEVICES to empty string."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    
    try:
        # Set a non-empty value
        os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2"
        assert os.environ["CUDA_VISIBLE_DEVICES"] != ""
        
        # Call the function
        enforce_cpu_only()
        
        # Verify it was set to empty
        assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value

def test_is_cpu_only_mode_returns_true_when_empty():
    """Test that is_cpu_only_mode returns True when CUDA_VISIBLE_DEVICES is empty."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    
    try:
        # Set to empty
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        assert is_cpu_only_mode() is True
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value

def test_is_cpu_only_mode_returns_false_when_set():
    """Test that is_cpu_only_mode returns False when CUDA_VISIBLE_DEVICES is set."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    
    try:
        # Set to non-empty
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        assert is_cpu_only_mode() is False
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value

def test_module_load_enforces_cpu():
    """Test that importing the module automatically enforces CPU-only mode."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    
    try:
        # Set to non-empty before import
        os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
        
        # Re-import the module to trigger the enforcement logic
        # Note: This test may need adjustment based on how the module is cached
        if 'src.utils.env_config' in sys.modules:
            del sys.modules['src.utils.env_config']
        
        from src.utils.env_config import is_cpu_only_mode
        
        # The module should have enforced CPU-only mode on import
        # However, since we set it before import, the module's initialization
        # should have already run. We need to check the current state.
        # The module's init code checks if the env var is not empty and sets it.
        # Since we set it before import, the module's init should have caught it.
        # But the check in the module is: if not set or not empty, set to empty.
        # So if we set it to "0,1" before import, the module should set it to "".
        assert is_cpu_only_mode() is True
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value

def test_log_environment_config():
    """Test that log_environment_config runs without errors."""
    # This test just verifies the function doesn't crash
    # Actual logging output is hard to capture in a simple test
    try:
        log_environment_config()
    except Exception as e:
        pytest.fail(f"log_environment_config raised an exception: {e}")
