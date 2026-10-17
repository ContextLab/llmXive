"""Test that the quickstart commands execute without error and produce expected files."""
from __future__ import annotations

import subprocess
from pathlib import Path

from llmxive_toolkit import paths

def test_smoke_test():
    """Run the smoke test and verify the placeholder file exists."""
    result = subprocess.run(
        [sys.executable, "-m", "code.run_pipeline", "--sample", "1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Smoke test failed: {result.stderr}"
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    assert out_path.exists(), f"Expected output not found: {out_path}"

def test_full_pipeline():
    """Run the full pipeline and verify that the commit‑pair CSV is created."""
    result = subprocess.run(
        [sys.executable, "-m", "code.run_pipeline", "--full"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Full pipeline failed: {result.stderr}"
    csv_path = paths.data("raw", "commit_pairs.csv")
    assert csv_path.exists(), f"Missing data file: {csv_path}"
    # Ensure at least the minimum number of rows (500) are present.
    with csv_path.open(newline="", encoding="utf-8") as f:
        line_count = sum(1 for _ in f) - 1  # subtract header
    assert line_count >= 500, f"Insufficient rows: {line_count}"