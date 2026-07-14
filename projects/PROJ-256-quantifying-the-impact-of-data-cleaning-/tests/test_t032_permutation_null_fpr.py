"""
Basic integration test for T032 – ensures that the null‑FPR generation script
runs without error and creates the expected JSON artifact.
"""

import json
import os
from pathlib import Path

import pytest

from t032_permutation_null_fpr import generate_null_fpr_metrics, main

@pytest.fixture(scope="module")
def raw_data_dir(tmp_path_factory):
    """
    Create a tiny synthetic raw dataset (real data is not required for the
    functionality test – the script only needs a CSV with at least one
    numeric predictor and an outcome column).  The fixture lives in a
    temporary directory that is cleaned up automatically.
    """
    base = tmp_path_factory.mktemp("raw")
    df_path = base / "dummy.csv"
    # Simple deterministic data
    import pandas as pd

    df = pd.DataFrame(
        {
            "outcome": [0, 1, 0, 1, 0],
            "feat1": [1, 2, 3, 4, 5],
            "feat2": [5, 4, 3, 2, 1],
        }
    )
    df.to_csv(df_path, index=False)
    return str(base)

def test_generate_null_fpr_metrics_creates_file(raw_data_dir, tmp_path):
    output_path = tmp_path / "null_fpr_metrics.json"
    metrics = generate_null_fpr_metrics(
        raw_dir=raw_data_dir,
        outcome="outcome",
        repetitions=10,
        output_file=str(output_path),
    )
    # Verify return structure
    assert isinstance(metrics, dict)
    assert "dummy.csv" in metrics
    assert len(metrics["dummy.csv"]) == 10

    # Verify file exists and is valid JSON
    assert output_path.is_file()
    with output_path.open() as f:
        content = json.load(f)
    assert content == metrics

def test_cli_entry_point(monkeypatch, raw_data_dir, tmp_path):
    """
    Run the module as a script via its ``main`` function, checking that it
    respects command‑line arguments and writes the expected file.
    """
    output_file = tmp_path / "cli_null_fpr.json"
    test_args = [
        "t032_permutation_null_fpr.py",
        "--raw-dir",
        raw_data_dir,
        "--outcome",
        "outcome",
        "--repetitions",
        "5",
        "--output",
        str(output_file),
    ]
    monkeypatch.setattr("sys.argv", test_args)
    # Importing the module runs the top‑level guard only when __name__ == "__main__"
    # so we call main() directly.
    main()
    assert output_file.is_file()
    with output_file.open() as f:
        data = json.load(f)
    assert "dummy.csv" in data
    assert len(data["dummy.csv"]) == 5