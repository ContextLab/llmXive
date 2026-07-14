"""
Tests for the flexible ``ensure_directories`` helper in ``config.py``.
"""

import shutil
from pathlib import Path

import pytest

from config import (
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    get_figures_dir,
    ensure_directories,
)


@pytest.fixture(autouse=True)
def clean_project_dirs(tmp_path: Path, monkeypatch):
    """
    Redirect all standard directories to a temporary location for isolation.
    """
    # Monkey‑patch the directory getters to point inside ``tmp_path``.
    monkeypatch.setattr("config.get_raw_dir", lambda: tmp_path / "data" / "raw")
    monkeypatch.setattr("config.get_processed_dir", lambda: tmp_path / "data" / "processed")
    monkeypatch.setattr("config.get_stratified_dir", lambda: tmp_path / "data" / "stratified")
    monkeypatch.setattr("config.get_features_dir", lambda: tmp_path / "data" / "features")
    monkeypatch.setattr("config.get_results_dir", lambda: tmp_path / "data" / "results")
    monkeypatch.setattr("config.get_figures_dir", lambda: tmp_path / "data" / "figures")

    yield

    # Cleanup after the test.
    if tmp_path.exists():
        shutil.rmtree(tmp_path)


def test_ensure_directories_no_args():
    """Calling without arguments should create all standard dirs."""
    created = ensure_directories()
    expected = {
        get_raw_dir(),
        get_processed_dir(),
        get_stratified_dir(),
        get_features_dir(),
        get_results_dir(),
        get_figures_dir(),
    }
    assert set(created) == expected
    for p in expected:
        assert p.is_dir()


def test_ensure_directories_single_path():
    """Calling with a single Path should create that directory only."""
    custom_dir = Path("some/custom/dir")
    created = ensure_directories(custom_dir)
    assert created == [custom_dir]
    assert custom_dir.is_dir()


def test_ensure_directories_iterable():
    """Calling with an iterable of Paths should create each of them."""
    dirs = [Path("a"), Path("b/c"), Path("d/e/f")]
    created = ensure_directories(dirs)
    assert set(created) == set(dirs)
    for p in dirs:
        assert p.is_dir()