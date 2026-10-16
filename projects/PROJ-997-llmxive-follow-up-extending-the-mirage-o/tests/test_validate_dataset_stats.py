"""
Unit test for T016 – validate_dataset_stats.py

The test runs the script on a tiny sample (10 GSM8K prompts) and checks
that the JSON output file is created and contains the expected keys.
"""

import json
from pathlib import Path
import subprocess
import sys

def test_validate_dataset_stats(tmp_path: Path):
    # Arrange: build arguments pointing to a temporary output location
    output_path = tmp_path / "dataset_stats.json"

    cmd = [
        sys.executable,
        "code/cli/validate_dataset_stats.py",
        "--model",
        "distilgpt2",
        "--levels",
        "INT8",
        "FP16",
        "--sample-size",
        "10",
        "--stats-output",
        str(output_path),
    ]

    # Act: run the script
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Debug output in case of failure
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Assert: output file exists and is valid JSON with the required structure
    assert output_path.is_file(), "dataset_stats.json was not created"

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic schema checks
    assert "per_level_statistics" in data, "Missing per_level_statistics"
    assert isinstance(data["per_level_statistics"], dict), "per_level_statistics should be a dict"
    for level, stats in data["per_level_statistics"].items():
        for key in ["sample_count", "mean_kl", "t_statistic", "p_value", "non_zero_fraction"]:
            assert key in stats, f"Missing {key} for level {level}"

    # The overall flag must be a boolean
    assert "overall_non_zero_kl_significant" in data
    assert isinstance(data["overall_non_zero_kl_significant"], bool)