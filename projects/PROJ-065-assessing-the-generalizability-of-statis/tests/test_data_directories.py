"""Tests to verify that the required data directories exist."""
from pathlib import Path
from llmxive_toolkit import paths

def test_raw_and_processed_directories_exist():
    """Both data/raw and data/processed directories should be present."""
    raw_dir: Path = paths.data("raw")
    processed_dir: Path = paths.data("processed")
    assert raw_dir.is_dir(), f"Raw data directory missing: {raw_dir}"
    assert processed_dir.is_dir(), f"Processed data directory missing: {processed_dir}"