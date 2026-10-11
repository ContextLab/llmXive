"""
Unit tests for the core download‑preprocess pipeline (T002).

The tests verify that the two scripts create the expected directory
structures and output files when run in CI mode.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_download_creates_raw_files(tmp_path: Path):
    # Run the download module
    result = subprocess.run(
        [sys.executable, "-m", "code.download", "--ci-mode"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Download script failed: {result.stderr}"

    raw_dir = paths.data("raw")
    expected_files = {"genotype.csv", "metabolomics.csv", "phenotype.csv"}
    assert raw_dir.is_dir(), "Raw data directory was not created."
    assert expected_files.issubset({p.name for p in raw_dir.iterdir()}), (
        f"Missing expected raw files. Found: {[p.name for p in raw_dir.iterdir()]}"
    )

def test_preprocess_creates_processed_file(tmp_path: Path):
    # Ensure raw files exist (run download first)
    subprocess.run(
        [sys.executable, "-m", "code.download", "--ci-mode"],
        cwd=Path.cwd(),
        check=True,
    )

    # Run the preprocess module
    result = subprocess.run(
        [sys.executable, "-m", "code.preprocess"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Preprocess script failed: {result.stderr}"

    processed_dir = paths.data("processed")
    expected_file = processed_dir / "combined_features.csv"
    assert expected_file.is_file(), "Processed combined_features.csv was not created."