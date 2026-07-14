"""
Unit tests for the ``ensure_directories`` helper in ``config.py``.
The tests exercise all supported call signatures.
"""

import os
import shutil
from pathlib import Path

import pytest

from config import (
    ensure_directories,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
)

@pytest.fixture(autouse=True)
def clean_project_dirs(tmp_path, monkeypatch):
    """
    Redirect all standard directories to a temporary location so the
    repository's real data is not polluted during the test run.
    """
    # Map the standard getters to temporary sub‑folders.
    temp_root = tmp_path / "proj"
    dirs = {
        "raw": temp_root / "data" / "raw",
        "processed": temp_root / "data" / "processed",
        "stratified": temp_root / "data" / "stratified",
        "features": temp_root / "data" / "features",
        "results": temp_root / "data" / "results",
    }

    # Monkey‑patch the getter functions to return the temporary paths.
    monkeypatch.setattr("config.get_raw_dir", lambda: dirs["raw"])
    monkeypatch.setattr("config.get_processed_dir", lambda: dirs["processed"])
    monkeypatch.setattr("config.get_stratified_dir", lambda: dirs["stratified"])
    monkeypatch.setattr("config.get_features_dir", lambda: dirs["features"])
    monkeypatch.setattr("config.get_results_dir", lambda: dirs["results"])

    # Ensure a clean slate before each test.
    for d in dirs.values():
        if d.exists():
            shutil.rmtree(d)
    yield
    # Cleanup after tests.
    for d in dirs.values():
        if d.exists():
            shutil.rmtree(d)

def test_create_all_standard_dirs():
    ensure_directories()
    assert get_raw_dir().exists()
    assert get_processed_dir().exists()
    assert get_stratified_dir().exists()
    assert get_features_dir().exists()
    assert get_results_dir().exists()

def test_create_single_path():
    custom = Path("tmp/single_dir")
    ensure_directories(custom)
    assert custom.is_dir()
    # Clean up
    shutil.rmtree(custom)

def test_create_multiple_paths():
    dirs = [Path("tmp/dir1"), Path("tmp/dir2")]
    ensure_directories(dirs)
    for d in dirs:
        assert d.is_dir()
    # Clean up
    for d in dirs:
        shutil.rmtree(d)