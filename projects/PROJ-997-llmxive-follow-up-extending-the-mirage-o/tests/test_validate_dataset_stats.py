"""
Unit test for ``code/cli/validate_dataset_stats.py``.

The test creates a tiny synthetic dataset (real values, not random
placeholders) that is sufficient to produce a statistically
significant KL divergence for one quantization level.  It then invokes
the validation script with a missing statistics file, verifies that the
script creates the JSON file, and checks that the exit status indicates
success.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the script as a module so we can invoke ``main`` directly.
from code.cli.validate_dataset_stats import main as validate_main


@pytest.fixture
def small_dataset(tmp_path: Path) -> Path:
    """
    Create a minimal parquet dataset with two quantization levels.
    INT8 contains non‑zero KL values that will be statistically
    significant; INT4 contains only zeros.
    """
    records = [
        {"input_id": 0, "quantization_level": "INT8", "gradient_norm": 1.0,
         "local_curvature": 1.0, "kl_divergence": 0.25},
        {"input_id": 1, "quantization_level": "INT8", "gradient_norm": 1.2,
         "local_curvature": 1.44, "kl_divergence": 0.30},
        {"input_id": 2, "quantization_level": "INT4", "gradient_norm": 0.8,
         "local_curvature": 0.64, "kl_divergence": 0.0},
        {"input_id": 3, "quantization_level": "INT4", "gradient_norm": 0.9,
         "local_curvature": 0.81, "kl_divergence": 0.0},
    ]
    df = pd.DataFrame.from_records(records)
    parquet_path = tmp_path / "training_sample.parquet"
    df.to_parquet(parquet_path, index=False)
    return parquet_path


def test_validate_creates_stats_and_passes(tmp_path: Path, small_dataset: Path):
    """
    Run the validation script when the statistics file is missing.
    The script should compute the statistics, write the JSON file, and
    exit with status 0 because INT8 achieves p < 0.05.
    """
    # Paths for the temporary stats file and the dataset.
    stats_path = tmp_path / "dataset_stats.json"

    # Build the argument list that mimics command‑line invocation.
    test_args = [
        "code/cli/validate_dataset_stats.py",
        f"--stats={stats_path}",
        f"--data={small_dataset}",
        "--alpha=0.05",
    ]

    # Patch ``sys.argv`` for the duration of the call.
    orig_argv = sys.argv
    sys.argv = test_args
    try:
        with pytest.raises(SystemExit) as exc_info:
            validate_main()
    finally:
        sys.argv = orig_argv

    # The script should have exited with code 0 (success).
    assert exc_info.value.code == 0

    # Verify that the statistics JSON file was created and contains the
    # expected structure.
    assert stats_path.is_file()
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)

    assert "per_level_statistics" in stats
    assert "INT8" in stats["per_level_statistics"]
    # The p‑value for INT8 must be less than the threshold.
    assert stats["per_level_statistics"]["INT8"]["p_value"] < 0.05
    # INT4 may be present but its p‑value will be > 0.05 (or omitted).