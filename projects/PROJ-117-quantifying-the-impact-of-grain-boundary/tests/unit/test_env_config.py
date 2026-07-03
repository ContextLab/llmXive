"""
Unit tests for environment variable configuration.
Verifies that the .env file exists and contains expected keys.
"""
import os
import pytest
from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"
REQUIRED_KEYS = ["MP_API_KEY", "OPENKIM_API_KEY"]


@pytest.fixture
def env_file_exists():
    return ENV_FILE_PATH.exists()


@pytest.fixture
def env_vars(env_file_exists):
    if not env_file_exists:
        return {}
    # Load .env manually without python-dotenv to avoid dependency issues in tests
    # if dotenv is not installed yet
    env_vars = {}
    with open(ENV_FILE_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
    return env_vars


def test_env_file_exists(env_file_exists):
    """Test that the .env file exists in the project root."""
    assert env_file_exists, ".env file must exist in the project root."


def test_required_api_keys_present(env_vars):
    """Test that all required API keys are defined in .env."""
    for key in REQUIRED_KEYS:
        assert key in env_vars, f"Required environment variable '{key}' is missing from .env."
        # Check that the value is not the placeholder string
        placeholder_values = [
            "YOUR_MATERIALS_PROJECT_API_KEY_HERE",
            "YOUR_OPENKIM_API_KEY_HERE",
            "YOUR_NIST_API_KEY_HERE"
        ]
        assert env_vars[key] not in placeholder_values, (
            f"API key '{key}' is set to a placeholder value. "
            "Please replace it with a valid key."
        )
