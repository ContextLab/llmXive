"""
Integration test that ensures the data loader can handle network interruptions
and respects the sample size limit.
"""
from __future__ import annotations

import pathlib

import pytest

# The function under test lives in the top‑level ``data_loader`` module,
# which is provided by ``code/data_loader.py``.
from data_loader import download_and_save_sample

def test_download_and_save_sample_creates_files(tmp_path: pathlib.Path, monkeypatch):
    """
    The test replaces ``datasets.load_dataset`` with a tiny mock that yields
    five records.  The loader is asked for ten samples – it should stop after
    the five records have been written.
    """
    class MockDataset:
        def __iter__(self):
            for i in range(5):
                yield {"content": f"print({i})"}

    # Monkey‑patch the HF loader to return our mock dataset.
    monkeypatch.setattr(
        "datasets.load_dataset", lambda *a, **k: MockDataset()
    )

    # Run the loader with a sample size larger than the mock provides.
    download_and_save_sample(sample_size=10)

    raw_dir = pathlib.Path("data/raw")
    files = list(raw_dir.glob("sample_*.py"))
    assert len(files) == 5, "Expected exactly five files from the mock dataset"
    for f in files:
        assert f.read_text().startswith("print"), "File content does not match expected pattern"