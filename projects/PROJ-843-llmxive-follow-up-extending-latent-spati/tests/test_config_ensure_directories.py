"""
Unit tests for the flexible ``ensure_directories`` function.

These tests verify that the function can be called with the various
signatures observed throughout the repository without raising
exceptions and that the expected directories are created.
"""

import shutil
from pathlib import Path

import pytest

# Import the function under test
from config import (
    ensure_directories,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
)

@pytest.fixture(autouse=True)
def clean_test_dirs(tmp_path: Path, monkeypatch):
    """
    Redirect all standard directories to a temporary location for isolation.
    """
    # Map each getter to a temporary sub‑directory.
    temp_dirs = {
        "raw": tmp_path / "raw",
        "processed": tmp_path / "processed",
        "stratified": tmp_path / "stratified",
        "features": tmp_path / "features",
        "results": tmp_path / "results",
    }

    # Patch the getter functions to return the temporary paths.
    monkeypatch.setattr("config.get_raw_dir", lambda: temp_dirs["raw"])
    monkeypatch.setattr("config.get_processed_dir", lambda: temp_dirs["processed"])
    monkeypatch.setattr("config.get_stratified_dir", lambda: temp_dirs["stratified"])
    monkeypatch.setattr("config.get_features_dir", lambda: temp_dirs["features"])
    monkeypatch.setattr("config.get_results_dir", lambda: temp_dirs["results"])

    # Ensure a clean slate before each test.
    for p in temp_dirs.values():
        if p.exists():
            shutil.rmtree(p)
    yield
    # Cleanup after tests.
    for p in temp_dirs.values():
        if p.exists():
            shutil.rmtree(p)

def test_ensure_directories_no_args():
    """Calling with no arguments should create all standard dirs."""
    ensure_directories()
    assert get_raw_dir().exists()
    assert get_processed_dir().exists()
    assert get_stratified_dir().exists()
    assert get_features_dir().exists()
    assert get_results_dir().exists()

def test_ensure_directories_single_path():
    """A single Path argument should be created."""
    custom = Path("custom_dir")
    ensure_directories(custom)
    assert custom.exists()
    # Standard dirs should NOT be created in this mode.
    assert not get_raw_dir().exists()

def test_ensure_directories_list():
    """A list of Paths should all be created."""
    dirs = [Path("a"), Path("b"), Path("c")]
    ensure_directories(dirs)
    for d in dirs:
        assert d.exists()
    assert not get_raw_dir().exists()

def test_ensure_directories_multiple_args():
    """Multiple Path arguments should all be created."""
    p1 = Path("p1")
    p2 = Path("p2")
    ensure_directories(p1, p2)
    assert p1.exists()
    assert p2.exists()
    assert not get_raw_dir().exists()

def test_ensure_directories_mixed():
    """Mixed positional and iterable arguments should be handled."""
    p1 = Path("m1")
    p2 = Path("m2")
    ensure_directories(p1, [p2, Path("m3")])
    assert p1.exists()
    assert p2.exists()
    assert Path("m3").exists()
    assert not get_raw_dir().exists()