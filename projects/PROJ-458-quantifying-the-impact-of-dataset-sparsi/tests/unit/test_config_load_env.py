"""
Unit tests for ``code/config.py`` – specifically the ``load_env`` function.

The tests verify that:
1. When ``MP_API_KEY`` is absent, ``load_env`` raises ``RuntimeError``.
2. When ``MP_API_KEY`` is present (either via the environment or a .env file),
   ``load_env`` returns the correct value.
"""

import os
import pathlib

import pytest

# Import the function under test. The project root is added to ``sys.path`` by the
# test runner, so a plain import works.
from config import load_env

def test_load_env_raises_when_key_missing(monkeypatch):
    """
    Ensure ``load_env`` aborts with a RuntimeError if ``MP_API_KEY`` is not set.
    """
    # Remove the variable if it exists in the environment.
    monkeypatch.delenv("MP_API_KEY", raising=False)

    # Ensure there is no .env file in the project root for this test.
    project_root = pathlib.Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    if env_path.is_file():
        # Temporarily rename the file so it is not discovered.
        temp_path = env_path.with_suffix(".bak")
        env_path.rename(temp_path)
        try:
            with pytest.raises(RuntimeError):
                load_env()
        finally:
            temp_path.rename(env_path)
    else:
        with pytest.raises(RuntimeError):
            load_env()

def test_load_env_returns_key_when_present(monkeypatch):
    """
    Verify that ``load_env`` returns the API key when it is defined in the
    environment.
    """
    test_key = "test_api_key_123"
    monkeypatch.setenv("MP_API_KEY", test_key)

    # The function should simply return the value we set.
    assert load_env() == test_key

def test_load_env_reads_from_dotenv_file(monkeypatch, tmp_path):
    """
    Confirm that ``load_env`` reads the key from a ``.env`` file when the
    environment variable is not otherwise set.
    """
    # Ensure the variable is not in the environment.
    monkeypatch.delenv("MP_API_KEY", raising=False)

    # Create a temporary .env file at the project root.
    project_root = pathlib.Path(__file__).resolve().parents[2]
    env_file = project_root / ".env"
    backup = None
    if env_file.is_file():
        backup = env_file.with_suffix(".bak")
        env_file.rename(backup)

    try:
        env_file.write_text("MP_API_KEY=dotenv_key_value\n")
        # Now ``load_env`` should pick up the value from the file.
        assert load_env() == "dotenv_key_value"
    finally:
        # Clean up the temporary .env file.
        if env_file.is_file():
            env_file.unlink()
        if backup and backup.is_file():
            backup.rename(env_file)