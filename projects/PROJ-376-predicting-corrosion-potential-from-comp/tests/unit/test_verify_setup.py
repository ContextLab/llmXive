"""
Unit tests for ``code.utils.verify_setup``.
The tests assume that a manifest file exists at ``state/setup_dirs_verified.json``.
They create a temporary manifest with the required entries, invoke the verification
logic, and ensure that it succeeds. A second test provides an incomplete manifest
and checks that a ``RuntimeError`` is raised.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the module under test.
from code.utils.verify_setup import (
    REQUIRED_DIRS,
    MANIFEST_PATH,
    load_manifest,
    verify,
)


def write_manifest(entries: list[dict], path: Path) -> None:
    """Helper to write a JSON manifest to ``path``."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(entries, f)


def test_verify_success(tmp_path: Path, monkeypatch):
    """Verification succeeds when all required directories are present."""
    # Build a manifest containing exactly the required directories.
    entries = [{"path": d, "created_at": "2024-01-01T00:00:00Z"} for d in REQUIRED_DIRS]

    # Write manifest to a temporary location and monkey‑patch the constant.
    temp_manifest = tmp_path / "setup_dirs_verified.json"
    write_manifest(entries, temp_manifest)
    monkeypatch.setattr("code.utils.verify_setup.MANIFEST_PATH", temp_manifest)

    # Should not raise.
    verify()


def test_verify_missing_directory(tmp_path: Path, monkeypatch):
    """Verification fails with a ``RuntimeError`` when a directory is missing."""
    # Omit one required directory.
    incomplete_dirs = set(list(REQUIRED_DIRS)[:-1])
    entries = [{"path": d, "created_at": "2024-01-01T00:00:00Z"} for d in incomplete_dirs]

    temp_manifest = tmp_path / "setup_dirs_verified.json"
    write_manifest(entries, temp_manifest)
    monkeypatch.setattr("code.utils.verify_setup.MANIFEST_PATH", temp_manifest)

    with pytest.raises(RuntimeError) as exc:
        verify()
    assert "Missing required directories" in str(exc.value)