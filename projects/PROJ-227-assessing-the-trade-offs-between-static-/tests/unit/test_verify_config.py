"""
Unit tests for verify_config.py logic.
"""
import pytest
import yaml
import tempfile
import os
from pathlib import Path

# Mock the main logic for testing without file system dependency
def validate_config_dict(config):
    """Replicate the validation logic from verify_config.py for testing."""
    if not isinstance(config, dict):
        return False, "Config root must be a dictionary"

    required_keys = {
        "human_eval_url": str,
        "codeql_path": str,
        "sonar_path": str,
        "max_cpu": int,
        "max_ram_gb": int,
    }

    errors = []
    for key, expected_type in required_keys.items():
        if key not in config:
            errors.append(f"Missing required key: {key}")
        elif not isinstance(config[key], expected_type):
            actual_type = type(config[key]).__name__
            errors.append(f"Key '{key}' has type {actual_type}, expected {expected_type.__name__}")

    if errors:
        return False, errors
    return True, []

def test_valid_config():
    config = {
        "human_eval_url": "https://example.com",
        "codeql_path": "/usr/bin/codeql",
        "sonar_path": "/usr/bin/sonar",
        "max_cpu": 4,
        "max_ram_gb": 16,
    }
    is_valid, errors = validate_config_dict(config)
    assert is_valid is True
    assert len(errors) == 0

def test_missing_key():
    config = {
        "human_eval_url": "https://example.com",
        "codeql_path": "/usr/bin/codeql",
        "sonar_path": "/usr/bin/sonar",
        "max_cpu": 4,
        # missing max_ram_gb
    }
    is_valid, errors = validate_config_dict(config)
    assert is_valid is False
    assert any("Missing required key: max_ram_gb" in e for e in errors)

def test_wrong_type():
    config = {
        "human_eval_url": "https://example.com",
        "codeql_path": "/usr/bin/codeql",
        "sonar_path": "/usr/bin/sonar",
        "max_cpu": "two",  # Should be int
        "max_ram_gb": 16,
    }
    is_valid, errors = validate_config_dict(config)
    assert is_valid is False
    assert any("has type str, expected int" in e for e in errors)

def test_not_dict():
    config = "string instead of dict"
    is_valid, errors = validate_config_dict(config)
    assert is_valid is False
    assert "Config root must be a dictionary" in errors

def test_yaml_parsing():
    yaml_content = """
    human_eval_url: "https://huggingface.co/datasets/openai/human-eval"
    codeql_path: "/usr/local/bin/codeql"
    sonar_path: "/opt/sonar-scanner/bin/sonar-scanner"
    max_cpu: 2
    max_ram_gb: 7
    """
    config = yaml.safe_load(yaml_content)
    is_valid, errors = validate_config_dict(config)
    assert is_valid is True
    assert config["max_cpu"] == 2
    assert config["max_ram_gb"] == 7