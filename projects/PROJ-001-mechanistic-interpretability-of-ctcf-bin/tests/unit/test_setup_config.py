"""
Unit test for the T009 configuration setup script.

The test executes the `setup_config.py` script, verifies that the
configuration file is created, and checks that the required keys are
present and correctly populated.
"""
import json
import os
from pathlib import Path

import yaml

import pytest

# Import the script's public function
from code.config.setup_config import generate_config, CONFIG_RELATIVE_PATH


@pytest.fixture(scope="function")
def clean_config_file(tmp_path):
    """
    Ensure a clean environment: remove any existing config file before
    each test and restore the original state afterwards.
    """
    # Determine absolute path of the config file within the project
    config_path = Path(__file__).resolve().parents[2] / CONFIG_RELATIVE_PATH
    # Backup if it already exists
    backup_path = None
    if config_path.is_file():
        backup_path = config_path.with_suffix(".bak")
        config_path.rename(backup_path)

    # Ensure removal
    if config_path.is_file():
        config_path.unlink()

    yield config_path

    # Cleanup after test
    if config_path.is_file():
        config_path.unlink()
    # Restore backup if there was one
    if backup_path and backup_path.is_file():
        backup_path.rename(config_path)


def test_generate_config_creates_file(clean_config_file):
    """
    Verify that `generate_config` creates the expected YAML file and that
    the file contains the required sections.
    """
    config_path = generate_config()
    assert config_path.is_file(), "Configuration file was not created"

    # Load YAML and validate structure
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Expected top‑level keys
    assert "api" in cfg, "Missing 'api' section in config"
    assert "data" in cfg, "Missing 'data' section in config"

    # API key placeholder should be a string (empty by default)
    assert isinstance(cfg["api"].get("encode_api_key", None), str)

    # Data paths must be strings and point to existing directories
    data_section = cfg["data"]
    for key in ("raw_dir", "processed_dir", "manifest_path"):
        assert key in data_section, f"Missing '{key}' in data section"
        path_obj = Path(data_section[key])
        # Directories should exist; manifest_path should be a file
        if key == "manifest_path":
            assert path_obj.is_file(), f"Manifest path does not exist: {path_obj}"
        else:
            assert path_obj.is_dir(), f"Data directory does not exist: {path_obj}"


def test_generate_config_idempotent(clean_config_file):
    """
    Running `generate_config` twice should not raise and should produce the
    same file contents.
    """
    first_path = generate_config()
    first_content = first_path.read_text(encoding="utf-8")

    second_path = generate_config()
    second_content = second_path.read_text(encoding="utf-8")

    assert first_path == second_path
    assert first_content == second_content, "Config file contents changed on re‑run"