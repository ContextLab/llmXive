"""
Unit tests for the configuration module.
Verifies that the CPU-only environment constraints are correctly applied.
"""
import os
import pytest
from utils.config import get_config, reset_config

def test_cpu_environment_vars_set():
    """Verify that CPU-only environment variables are set."""
    # Check that CUDA is disabled
    assert os.getenv("CUDA_VISIBLE_DEVICES") == ""
    
    # Check thread limits
    assert os.getenv("OMP_NUM_THREADS") == "2"
    assert os.getenv("MKL_NUM_THREADS") == "2"

def test_config_loads_successfully():
    """Verify that the config module loads without error."""
    # Reset config to ensure clean state
    reset_config()
    
    # Load config
    config = get_config()
    
    # Basic assertions
    assert config is not None
    assert hasattr(config, 'get_target_countries')
