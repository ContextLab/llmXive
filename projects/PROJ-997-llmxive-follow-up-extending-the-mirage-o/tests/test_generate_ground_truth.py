"""
Unit test for the generate_ground_truth script (T015).

The test runs the script on a very small sample (10 prompts) and checks that
the expected output files are created and contain plausible data.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Helper to invoke the CLI script
def run_script(args: list) -> subprocess.CompletedProcess:
    """Run the generate_ground_truth.py script with the given args."""
    cmd = [sys.executable, "code/cli/generate_ground_truth.py"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,  # let the test assert on returncode
    )

@pytest.mark.timeout(540)
def test_generate_ground_truth_small_run(tmp_path: Path):
    """
    Execute the script on a tiny subset and verify that the parquet and
    stats JSON files are written and contain the expected keys.
    """
    parquet_file = tmp_path / "training_sample.parquet"
    stats_file = tmp_path / "dataset_stats.json"

    # Use a very small sample size to keep CI runtime low.
    args = [
        "--model",
        "meta-llama/Meta-Llama-3-8B",
        "--levels",
        "INT8",
        "FP16",
        "--sample-size",
        "10",
        "--output",
        str(parquet_file),
        "--stats-output",
        str(stats_file),
    ]

    result = run_script(args)

    # The script should exit with code 0.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that both output files exist.
    assert parquet_file.is_file(), "Parquet output file was not created."
    assert stats_file.is_file(), "Stats JSON file was not created."

    # Basic sanity checks on the parquet content.
    import pandas as pd

    df = pd.read_parquet(parquet_file)
    # Expect columns defined in the script.
    expected_cols = {
        "input_id",
        "quantization_level",
        "gradient_norm",
        "local_curvature",
        "kl_divergence",
    }
    assert set(df.columns) == expected_cols
    # There should be exactly 2 * sample_size rows (one per quantization level).
    assert len(df) == 20

    # Verify JSON structure.
    with open(stats_file, "r", encoding="utf-8") as f:
        stats = json.load(f)

    assert "per_level_statistics" in stats
    assert "overall_non_zero_kl_significant" in stats
    # Each requested level must be present.
    for level in ["INT8", "FP16"]:
        assert level in stats["per_level_statistics"]
        level_stats = stats["per_level_statistics"][level]
        for key in ["sample_count", "mean_kl", "t_statistic", "p_value", "non_zero_fraction"]:
            assert key in level_stats
