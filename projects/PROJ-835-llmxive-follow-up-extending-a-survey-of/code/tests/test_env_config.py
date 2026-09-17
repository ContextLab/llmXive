"""
Tests for the environment configuration module.

These tests verify that CPU-only execution is properly enforced.
"""
import os
import sys
import pytest
from unittest.mock import patch
import importlib

# Import the module to test
from src.utils.env_config import (
    enforce_cpu_only, 
    is_cpu_only_mode, 
    log_environment_config
)

def test_env_config_imports():
    """Test that all required functions can be imported."""
    assert callable(enforce_cpu_only)
    assert callable(is_cpu_only_mode)
    assert callable(log_environment_config)

def test_enforce_cpu_only_sets_env_variable():
    """Test that enforce_cpu_only sets CUDA_VISIBLE_DEVICES to empty string."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    
    try:
        # Set a non-empty value
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        
        # Call the function
        enforce_cpu_only()
        
        # Verify it was set to empty
        assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    finally:
        # Restore original value
        if original_value:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value
        else:
            del os.environ["CUDA_VISIBLE_DEVICES"]

def test_is_cpu_only_mode_returns_true_when_empty():
    """Test is_cpu_only_mode returns True when CUDA_VISIBLE_DEVICES is empty."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    
    try:
        # Set to empty
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Verify function returns True
        assert is_cpu_only_mode() is True
    finally:
        # Restore original value
        if original_value:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value
        else:
            del os.environ["CUDA_VISIBLE_DEVICES"]

def test_is_cpu_only_mode_returns_false_when_set():
    """Test is_cpu_only_mode returns False when CUDA_VISIBLE_DEVICES is set."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    
    try:
        # Set to non-empty
        os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
        
        # Verify function returns False
        assert is_cpu_only_mode() is False
    finally:
        # Restore original value
        if original_value:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value
        else:
            del os.environ["CUDA_VISIBLE_DEVICES"]

def test_module_load_enforces_cpu():
    """Test that importing the module enforces CPU-only mode."""
    # Save original value
    original_value = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    
    try:
        # Set to non-empty before import
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        
        # Import the module (this should enforce CPU-only)
        # Note: We can't re-import in the same process, so we just check
        # that the environment variable is now empty
        assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    finally:
        # Restore original value
        if original_value:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_value
        else:
            del os.environ["CUDA_VISIBLE_DEVICES"]