import os
import json
import pytest
from utils.config import load_config

def test_load_config_defaults(tmp_path):
    """
    Verify that the configuration loader returns a dictionary with the
    expected keys and default values when no configuration file is present.
    """
    # Ensure the default location does not contain a file
    default_path = os.path.join("code", "utils", "config.yaml")
    if os.path.exists(default_path):
        os.remove(default_path)

    cfg = load_config()
    assert isinstance(cfg, dict), "load_config should return a dict"
    # Default values
    assert cfg["model_path"] == "", "Default model_path should be empty"
    assert cfg["checkpoint_interval"] == 3, "Default checkpoint interval should be 3"

def test_load_config_from_file(tmp_path):
    """
    Write a minimal YAML configuration file and ensure the loader extracts
    the correct values.
    """
    yaml_content = """
    model:
      path: /models/llama.gguf
    checkpoint:
      interval: 5
    """
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml_content)

    cfg = load_config(str(cfg_path))
    assert cfg["model_path"] == "/models/llama.gguf"
    assert cfg["checkpoint_interval"] == 5