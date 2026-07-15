"""
Basic integration test for T023 – ensures that the cleaned‑metrics JSON file is
produced and contains at least one entry with valid numeric values.
"""
import json
import os
from pathlib import Path

import pandas as pd

from t023_reanalyze_cleaned_variants import main as t023_main
from utils import setup_logging, pin_random_seed

def test_cleaned_metrics_generated(tmp_path, monkeypatch):
    # Create a tiny synthetic cleaned dataset (real data not required for the test,
    # but the analysis code works on any numeric CSV).
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    test_csv = processed_dir / "dummy_cleaned.csv"
    df = pd.DataFrame({
        "outcome": [1, 2, 3, 4, 5],
        "predictor1": [5, 4, 3, 2, 1],
        "predictor2": [2, 3, 2, 3, 2],
    })
    df.to_csv(test_csv, index=False)

    # Run the script
    t023_main()

    # Verify output file exists and contains valid data
    output_file = processed_dir / "cleaned_metrics.json"
    assert output_file.is_file(), "cleaned_metrics.json was not created"

    with open(output_file) as f:
        data = json.load(f)

    # At least one entry should be present
    assert "dummy_cleaned.csv" in data

    metrics = data["dummy_cleaned.csv"]
    # Check that a p‑value exists and is within (0,1)
    p_val = metrics["t_test"]["p_value"]
    assert 0.0 < p_val < 1.0, f"Invalid p‑value {p_val}"
    # Linear regression p‑value also in (0,1)
    lr_p = metrics["linear_regression"]["p_value"]
    assert 0.0 < lr_p < 1.0, f"Invalid linear regression p‑value {lr_p}"
