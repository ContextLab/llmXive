"""
Test suite for the environment‑check script (task T001).

The test verifies three things:
1. The script can be executed as a module (``python -m src.env_check``) and exits with status 0.
2. The global configuration module defines ``SEED``.
3. The SHA‑256 checksums written to ``data/raw/checksums.json`` match the
   actual contents of the bundled raw CSV files.
"""

import json
import subprocess
import sys
import hashlib
from pathlib import Path

import pytest


def _compute_sha256(path: Path) -> str:
    """Return the SHA‑256 checksum of the file at *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_env_check_exits_successfully():
    """Run the env_check module and ensure it exits with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "src.env_check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_config_defines_seed():
    """The configuration module must expose a reproducible SEED."""
    from src import config

    assert hasattr(config, "SEED"), "config.SEED is missing"
    # The seed should be an int for reproducibility.
    assert isinstance(config.SEED, int)


def test_checksums_match_files():
    """Validate that the JSON of checksums corresponds to the actual files."""
    checksums_path = Path("data/raw/checksums.json")
    assert checksums_path.is_file(), "checksums.json does not exist"

    with checksums_path.open(encoding="utf-8") as f:
        recorded = json.load(f)

    for filename, recorded_checksum in recorded.items():
        file_path = Path("data/raw") / filename
        assert file_path.is_file(), f"Raw file {filename} is missing"
        actual_checksum = _compute_sha256(file_path)
        assert actual_checksum == recorded_checksum, (
            f"Checksum mismatch for {filename}: "
            f"expected {recorded_checksum}, got {actual_checksum}"
        )