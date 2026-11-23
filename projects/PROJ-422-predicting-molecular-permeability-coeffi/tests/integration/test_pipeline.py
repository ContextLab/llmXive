"""
Integration test that runs the full pipeline via ``run_all.sh`` and
checks that the essential artefacts exist.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(600)
def test_full_pipeline():
    # Execute the driver script
    result = subprocess.run(
        ["bash", "run_all.sh"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"run_all.sh failed: {result.stderr}"

    # Verify key artefacts
    expected_files = [
        paths.data("raw", "permeability_data.csv"),
        paths.data("raw", "checksums.json"),
        paths.data("processed", "processed_data.parquet"),
        paths.data("processed", "train.parquet"),
        paths.data("processed", "test.parquet"),
        paths.code("models", "gnn.pt"),
        paths.code("models", "rf.pkl"),
        paths.results("metrics.json"),
        paths.results("training_log.json"),
        paths.results("results.md"),
    ]

    for p in expected_files:
        assert p.is_file(), f"Expected file not found: {p}"