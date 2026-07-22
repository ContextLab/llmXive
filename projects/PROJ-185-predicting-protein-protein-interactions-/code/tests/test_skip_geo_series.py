"""
Unit test for the GEO downloader skip‑logic (T043).

The test patches network calls so that no real HTTP request is performed.
It verifies that a series with <30 samples produces a warning in the
pipeline log and that the checksum file is *not* created for the skipped
series.
"""
import json
import os
from pathlib import Path
from unittest import mock

import pytest

from src.pipeline.download import process_series, build_parser

@pytest.fixture
def clean_state(tmp_path):
    # Ensure a clean ``state`` directory for each test
    state_dir = Path("state")
    if state_dir.exists():
        for p in state_dir.iterdir():
            p.unlink()
    state_dir.mkdir(exist_ok=True)
    yield
    # Cleanup after test
    for p in state_dir.iterdir():
        p.unlink()

@pytest.fixture
def clean_log(tmp_path):
    log_path = Path("pipeline.log")
    if log_path.exists():
        log_path.unlink()
    yield
    if log_path.exists():
        log_path.unlink()

def fake_summary_small(*args, **kwargs):
    # Return a summary dict indicating 10 samples
    return {"samplecount": 10}

def fake_summary_large(*args, **kwargs):
    # Return a summary dict indicating 50 samples
    return {"samplecount": 50}

def fake_download(*args, **kwargs):
    # Simulate a successful download by creating an empty file
    dest_path = args[1] / "GSE99999_series_matrix.txt.gz"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.touch()
    return dest_path

def test_skip_series_with_few_samples(monkeypatch, clean_state, clean_log):
    # Patch the network helpers
    monkeypatch.setattr(
        "src.pipeline.download._fetch_series_summary", lambda gid: {"samplecount": 5}
    )
    # Run the processing function
    args = mock.MagicMock()
    args.seed = 123
    process_series("GSE99999", args)

    # Verify that a warning was written to the log
    log_contents = Path("pipeline.log").read_text()
    assert "Skipping GEO series GSE99999: only 5 samples (< 30)" in log_contents

    # Verify that no checksum entry was created
    hash_file = Path("state/artifact_hashes.yaml")
    assert not hash_file.exists() or "GSE99999" not in json.loads(hash_file.read_text())

def test_process_series_with_enough_samples(monkeypatch, clean_state, clean_log):
    # Patch helpers to simulate a large series and a dummy download
    monkeypatch.setattr(
        "src.pipeline.download._fetch_series_summary", lambda gid: {"samplecount": 40}
    )
    monkeypatch.setattr(
        "src.pipeline.download._download_series_matrix", fake_download
    )
    args = mock.MagicMock()
    args.seed = 123
    process_series("GSE88888", args)

    # Log should contain a success message
    log_contents = Path("pipeline.log").read_text()
    assert "Successfully downloaded GSE88888" in log_contents

    # Check that a checksum entry now exists
    hash_file = Path("state/artifact_hashes.yaml")
    assert hash_file.is_file()
    data = json.loads(hash_file.read_text())
    assert "GSE88888" in data
    # The checksum should be a 64‑character hex string
    assert len(data["GSE88888"]) == 64