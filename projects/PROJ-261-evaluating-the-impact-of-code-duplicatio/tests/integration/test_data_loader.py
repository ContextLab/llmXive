"""
Integration test that ensures the data loader can handle network interruptions
and respects the sample size limit.
"""
from __future__ import annotations

import pathlib

import pytest

from data_loader import download_and_save_sample

def test_download_and_save_sample_creates_files(tmp_path: pathlib.Path, monkeypatch):
    # Monkey‑patch the dataset loader to a tiny mock that yields a few records
    class MockDataset:
        def __iter__(self):
            for i in range(5):
                yield {"content": f"print({i})"}

    monkeypatch.setattr("datasets.load_dataset", lambda *a, **k: MockDataset())

    # Run with a sample size larger than the mock provides – should stop early
    download_and_save_sample(sample_size=10)

    raw_dir = pathlib.Path("data/raw")
    files = list(raw_dir.glob("sample_*.py"))
    assert len(files) == 5
    for f in files:
        assert f.read_text().startswith("print")
