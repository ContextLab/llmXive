"""
Unit test for the ground‑truth generation wrapper.

It verifies that:
  * The wrapper creates the expected Parquet file.
  * The statistics JSON file is written.
  * At least one quantization level reports a statistically significant
    KL divergence (p < 0.05).

The test uses a very small sample size to keep runtime low while still
exercising the real data‑download and model‑loading logic.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Helper to invoke the wrapper script
def run_wrapper(tmp_path: Path, sample_size: int = 10):
    parquet_path = tmp_path / "training_sample.parquet"
    cmd = [
        sys.executable,
        "code/data/generate_ground_truth.py",
        "--model",
        "distilgpt2",                 # small fallback model guaranteed to exist
        "--levels",
        "INT8",
        "FP8",
        "--output",
        str(parquet_path),
        "--sample-size",
        str(sample_size),
    ]
    result = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result, parquet_path

def test_wrapper_creates_outputs(tmp_path: Path):
    result, parquet_path = run_wrapper(tmp_path, sample_size=5)

    # The script should exit cleanly
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Parquet file must exist and contain rows
    assert parquet_path.is_file(), "Parquet output not created"
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
    except Exception as exc:
        pytest.fail(f"Failed to read Parquet file: {exc}")
    assert len(df) > 0, "Parquet file is empty"

    # Statistics JSON must exist
    stats_path = Path("data/processed/dataset_stats.json")
    assert stats_path.is_file(), "Statistics JSON not created"

    # Load and verify JSON content
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)

    per_level = stats.get("per_level_statistics", {})
    assert per_level, "No per‑level statistics found"

    # At least one level should have p < 0.05
    significant = any(
        level_info.get("p_value", 1) < 0.05 for level_info in per_level.values()
    )
    assert significant, "No quantization level achieved statistical significance"

# Clean up generated files after the test run
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Remove the generated stats file if it exists
    stats_file = Path("data/processed/dataset_stats.json")
    if stats_file.is_file():
        stats_file.unlink()
    # Remove any parquet files created in the project root
    for p in Path(".").rglob("*.parquet"):
        try:
            p.unlink()
        except Exception:
            pass