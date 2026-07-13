"""
Unit tests for ``data_loader.download_and_save_sample``.
The function must accept both positional and keyword calls.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from data_loader import download_and_save_sample

@pytest.fixture(scope="function")
def clean_raw_dir(tmp_path: Path, monkeypatch):
    """Ensure the ``data/raw`` directory starts empty."""
    raw_dir = Path("data/raw")
    if raw_dir.is_dir():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Monkey‑patch the dataset loading to avoid network calls in CI.
    class DummyDataset:
        def __init__(self, size):
            self._size = size

        def __iter__(self):
            for i in range(self._size):
                yield {
                    "repo_name": f"repo{i}",
                    "file_path": f"file{i}.py",
                    "content": f"print({i})",
                }

    monkeypatch.setattr("data_loader.load_dataset", lambda *args, **kwargs: DummyDataset(5))
    yield raw_dir
    shutil.rmtree(raw_dir, ignore_errors=True)

def test_download_default(clean_raw_dir):
    """Default call (no args) should create a CSV with the default size."""
    download_and_save_sample()
    csv_path = Path("data/raw/github-code-sample.csv")
    assert csv_path.is_file()
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5  # matches the dummy size

def test_download_with_keyword(clean_raw_dir):
    """Keyword argument should be respected."""
    download_and_save_sample(sample_size=3)
    csv_path = Path("data/raw/github-code-sample.csv")
    assert csv_path.is_file()
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3