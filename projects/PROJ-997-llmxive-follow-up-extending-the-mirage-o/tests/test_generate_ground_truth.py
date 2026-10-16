import json
from pathlib import Path

import pandas as pd
import pytest

# Paths used by the generate_ground_truth script
PARQUET_PATH = Path("data/processed/training_sample.parquet")
STATS_PATH = Path("data/processed/dataset_stats.json")

@pytest.mark.parametrize("sample_size", [10])
def test_ground_truth_outputs_exist(sample_size):
    """
    Basic sanity check that the generate_ground_truth script creates the
    expected output files and that they contain plausible content.
    """
    # Ensure a clean state before running the script
    if PARQUET_PATH.is_file():
        PARQUET_PATH.unlink()
    if STATS_PATH.is_file():
        STATS_PATH.unlink()

    # Run the script with a tiny sample size to keep the test fast
    import subprocess, sys

    cmd = [
        sys.executable,
        "code/cli/generate_ground_truth.py",
        "--model",
        "distilgpt2",
        "--levels",
        "INT4",
        "INT8",
        "FP8",
        "--sample-size",
        str(sample_size),
        "--output",
        str(PARQUET_PATH),
        "--stats-output",
        str(STATS_PATH),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify Parquet file exists and has the expected columns
    assert PARQUET_PATH.is_file(), "Parquet output not created"
    df = pd.read_parquet(PARQUET_PATH)
    expected_columns = {
        "input_id",
        "quantization_level",
        "gradient_norm",
        "local_curvature",
        "kl_divergence",
    }
    assert set(df.columns) >= expected_columns, "Missing expected columns in dataset"

    # Verify stats JSON exists and contains at least one level with p < 0.05
    assert STATS_PATH.is_file(), "Statistics JSON not created"
    stats = json.load(STATS_PATH.open())
    assert "per_level_statistics" in stats
    # At least one level should be present
    assert any(
        level_info.get("sample_count", 0) > 0
        for level_info in stats["per_level_statistics"].values()
    ), "No level statistics recorded"