"""Tests for T003c: verification that code/.ruff.toml exists after T003a."""

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE_DIR))

from validation import verify_ruff_config  # noqa: E402


def test_verify_ruff_config_passes_when_file_exists():
    assert verify_ruff_config() is True


def test_verify_ruff_config_fails_loudly_when_missing():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / ".ruff.toml"
        with pytest.raises(FileNotFoundError) as excinfo:
            verify_ruff_config(missing)
        assert "T003a" in str(excinfo.value)
        assert ".ruff.toml" in str(excinfo.value)