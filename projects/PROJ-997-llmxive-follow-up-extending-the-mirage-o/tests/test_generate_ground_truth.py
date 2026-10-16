"""
Unit tests for the ground‑truth generation wrapper.

The tests run the wrapper on a very small sample (10 prompts) to ensure
that the script completes without error and produces both expected output
files.  The test uses the real GSM8K dataset streamed from Hugging Face,
so it validates the end‑to‑end data pipeline on real data.
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# The wrapper script is executed as a subprocess in the test harness.
# The quick‑start command is reproduced here with a tiny sample size
# to keep the test runtime short.
@pytest.mark.timeout(300)
def test_generate_ground_truth_wrapper(tmp_path, subprocess):
    # Define output locations inside the temporary directory
    parquet_file = tmp_path / "training_sample.parquet"
    stats_file = tmp_path / "dataset_stats.json"

    # Build the command
    cmd = [
        "python",
        "code/data/generate_ground_truth.py",
        "--model",
        "distilgpt2",          # small model guaranteed to load quickly
        "--levels",
        "INT8",
        "FP8",
        "--output",
        str(parquet_file),
        "--sample-size",
        "10",
    ]

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Ensure the script exited cleanly
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify both output files exist
    assert parquet_file.is_file(), "Parquet dataset not created"
    assert stats_file.is_file(), "Statistics JSON not created"

    # Load the JSON and perform a minimal sanity check
    with open(stats_file, "r", encoding="utf-8") as f:
        stats = json.load(f)

    # At least one quantisation level should be present
    assert "per_level_statistics" in stats
    assert isinstance(stats["per_level_statistics"], dict)
    # The sample count for the used level should match the number of prompts
    level_stats = stats["per_level_statistics"].get("INT8")
    assert level_stats is not None
    assert level_stats["sample_count"] == 10