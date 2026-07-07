"""
Tests for the code/config.py module.
Verifies that constants are defined correctly and directories are created.
"""
import os
import pytest
from pathlib import Path

# Import the config module
from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    FIGURES_DIR,
    MODEL_CONFIG,
    MODEL_KEYS,
    SEED,
    TEMPERATURE,
    MAX_NEW_TOKENS,
    NULL_ENERGY_VALUE,
    DEVICE
)

def test_directories_exist():
    """Ensure that the data and figures directories are created upon import."""
    assert DATA_RAW_DIR.exists(), f"Directory {DATA_RAW_DIR} should exist"
    assert DATA_PROCESSED_DIR.exists(), f"Directory {DATA_PROCESSED_DIR} should exist"
    assert FIGURES_DIR.exists(), f"Directory {FIGURES_DIR} should exist"
    assert DATA_RAW_DIR.is_dir(), f"{DATA_RAW_DIR} should be a directory"
    assert DATA_PROCESSED_DIR.is_dir(), f"{DATA_PROCESSED_DIR} should be a directory"
    assert FIGURES_DIR.is_dir(), f"{FIGURES_DIR} should be a directory"

def test_model_keys():
    """Verify that the expected model keys are present."""
    expected_keys = {"gpt2", "codebert", "starcoder_1b"}
    assert set(MODEL_KEYS) == expected_keys, f"Model keys mismatch: {set(MODEL_KEYS)} vs {expected_keys}"

def test_model_config_structure():
    """Verify that each model has the required configuration fields."""
    required_fields = {"model_id", "parameter_count", "max_tokens", "temperature", "description"}
    
    for key in MODEL_KEYS:
        assert key in MODEL_CONFIG, f"Model {key} not found in MODEL_CONFIG"
        config = MODEL_CONFIG[key]
        assert required_fields.issubset(config.keys()), f"Missing fields in {key} config: {required_fields - set(config.keys())}"
        
        # Specific type checks
        assert isinstance(config["parameter_count"], int), f"parameter_count for {key} must be int"
        assert isinstance(config["max_tokens"], int), f"max_tokens for {key} must be int"
        assert isinstance(config["temperature"], float), f"temperature for {key} must be float"

def test_starcoder_1b_config():
    """Specific check for StarCoder-1B configuration."""
    starcoder = MODEL_CONFIG.get("starcoder_1b")
    assert starcoder is not None, "starcoder_1b must be configured"
    # The task specifically requested StarCoder-1B
    assert "1b" in starcoder["model_id"].lower() or "starcoderbase-1b" in starcoder["model_id"].lower(), \
        f"StarCoder model ID should indicate 1B variant, got: {starcoder['model_id']}"

def test_inference_params():
    """Verify inference parameters are set as per task requirements."""
    assert TEMPERATURE == 0.0, "Temperature must be 0.0"
    assert MAX_NEW_TOKENS == 50, "Max new tokens must be 50"
    assert SEED == 42, "Seed must be 42"

def test_device_constraint():
    """Verify that the device is set to CPU."""
    assert DEVICE == "cpu", "Device must be set to 'cpu' for this project"

def test_null_values():
    """Verify null placeholders are defined."""
    assert NULL_ENERGY_VALUE is None, "NULL_ENERGY_VALUE should be None"

def test_project_root():
    """Verify project root is a valid Path object."""
    assert isinstance(PROJECT_ROOT, Path), "PROJECT_ROOT must be a Path object"
    assert PROJECT_ROOT.exists(), "PROJECT_ROOT path must exist"
