"""
Unit test for the permutation‑null FPR generation script (T032).

The test creates a tiny synthetic CSV dataset in ``data/raw``,
runs the ``generate_null_fpr_metrics`` function, and checks that:
  * The output JSON file is created.
  * The JSON contains the expected top‑level keys.
  * The per‑dataset FPR is a float between 0 and 1.
The synthetic data is deliberately tiny but valid; the test does not
rely on any external network resources.
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from t032_permutation_null_fpr import generate_null_fpr_metrics

@pytest.fixture
def tiny_dataset(tmp_path):
    """Create a minimal CSV file with a clear outcome column."""
    df = pd.DataFrame(
        {
            "target": [0, 1, 0, 1, 0, 1],
            "feature1": [5, 3, 6, 2, 7, 1],
            "feature2": [10, 20, 10, 20, 10, 20],
        }
    )
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    csv_path = raw_dir / "tiny.csv"
    df.to_csv(csv_path, index=False)
    return raw_dir

def test_generate_null_fpr_metrics_creates_output(tiny_dataset, tmp_path):
    output_path = tmp_path / "processed" / "null_fpr_metrics.json"

    # Run the function with a small number of permutations for speed
    result = generate_null_fpr_metrics(
        raw_dir=tiny_dataset,
        output_file=output_path,
        n_permutations=200,
        alpha=0.05,
    )

    # Verify the JSON file exists and is loadable
    assert output_path.is_file(), "Output JSON file was not created"
    with open(output_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    # Basic structural checks
    assert "metadata" in loaded
    assert "datasets" in loaded
    assert "overall_fpr" in loaded

    # There should be exactly one dataset entry
    assert list(loaded["datasets"].keys()) == ["tiny.csv"]

    dataset_metrics = loaded["datasets"]["tiny.csv"]
    # FPR should be a float between 0 and 1
    fpr = dataset_metrics.get("fpr")
    assert isinstance(fpr, float)
    assert 0.0 <= fpr <= 1.0

    # The function's return value should match the file contents
    assert result == loaded