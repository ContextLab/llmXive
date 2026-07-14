"""
Simple integration test for T032 – ensures that the null‑FPR generation script
creates the expected JSON artifact without raising exceptions.
"""

import json
import os
from pathlib import Path

import pytest

# Import the function directly for a lightweight test
from t032_permutation_null_fpr import generate_null_fpr_metrics

@pytest.fixture(scope="module")
def raw_data_dir(tmp_path_factory):
    """
    Create a tiny synthetic raw dataset (real data not required for the test of
    the pipeline mechanics). The dataset is written to a temporary directory
    that mimics ``data/raw``.
    """
    dir_path = tmp_path_factory.mktemp("raw")
    df = (
        pd.DataFrame(
            {
                "outcome": [0, 1, 0, 1, 0],
                "feat1": [1.2, 2.3, 1.5, 2.1, 1.0],
                "feat2": [3.4, 3.5, 3.1, 3.8, 3.0],
            }
        )
        .astype({"outcome": int, "feat1": float, "feat2": float})
    )
    csv_path = dir_path / "dummy.csv"
    df.to_csv(csv_path, index=False)
    return dir_path

def test_generate_null_fpr_metrics_creates_file(raw_data_dir, tmp_path):
    output_path = tmp_path / "null_fpr_metrics.json"
    # Run the generator
    result = generate_null_fpr_metrics(
        raw_dir=Path(raw_data_dir),
        outcome_column="outcome",
        output_path=output_path,
        seed=123,
    )
    # Verify the file exists
    assert output_path.is_file(), "Null FPR JSON file was not created."

    # Load the file and compare with the returned dict
    with open(output_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded == result, "Returned dict does not match written JSON."

    # Basic sanity check on content
    assert "dummy.csv" in loaded, "Expected dataset key missing in output."
    metrics = loaded["dummy.csv"]
    assert "t_test" in metrics and "regression" in metrics, "Metrics structure incomplete."