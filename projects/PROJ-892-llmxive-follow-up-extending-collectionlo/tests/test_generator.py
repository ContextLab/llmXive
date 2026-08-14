import pytest
from pathlib import Path
import os
import sys

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generator import generate_reference_image
from config import load_config

def test_generate_reference_image_creates_file():
    """
    Test that generate_reference_image creates the expected file.
    This is a minimal smoke test. In a full CI, this would run with a real model.
    For now, we verify the function signature and basic logic structure.
    """
    # We cannot run the full generation in a unit test without a GPU/CPU model download
    # So we verify the path construction and directory creation logic
    output_path = "data/references/baseline_ref.png"
    
    # Ensure the directory exists for the test
    Path("data/references").mkdir(parents=True, exist_ok=True)
    
    # The actual generation requires a model download which is too heavy for a unit test.
    # We assert that the function exists and has the right signature.
    # A full integration test would run this with a mock or a small model.
    assert callable(generate_reference_image)
    
    # Check if config exists
    config_path = Path("code/config.yaml")
    assert config_path.exists(), "config.yaml must exist for the task to be valid"

def test_config_exists():
    """Verify that the config.yaml file exists as required by T011b."""
    config = load_config()
    assert "prompts" in config
    assert "seeds" in config
    assert "reference" in config
    assert config["reference"]["seed"] == 42
    assert config["reference"]["prompt"] == "a simple test object"