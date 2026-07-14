"""
Unit test for the T023 re‑analysis script.

The test creates a tiny synthetic cleaned CSV file, runs the script,
and checks that ``cleaned_metrics.json`` is produced and contains
a valid JSON object.
"""

import json
import os
from pathlib import Path

import pandas as pd

import sys

# Ensure the project root is on the path so imports work
sys.path.append(str(Path(__file__).resolve().parents[2]))

from t023_reanalyze_cleaned_variants import main as reanalyse_main


def test_reanalyse_creates_cleaned_metrics(tmp_path):
    # Arrange: create a minimal cleaned CSV in the expected location
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    csv_path = processed_dir / "sample_cleaned.csv"
    df = pd.DataFrame(
        {
            "outcome": [0, 1, 0, 1],
            "feat1": [1.2, 2.3, 1.1, 2.0],
            "feat2": [3.4, 3.5, 3.3, 3.6],
        }
    )
    df.to_csv(csv_path, index=False)

    # Act: run the re‑analysis script
    reanalyse_main()

    # Assert: cleaned_metrics.json exists and is valid JSON
    metrics_path = processed_dir / "cleaned_metrics.json"
    assert metrics_path.is_file(), "cleaned_metrics.json was not created"

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "sample_cleaned.csv" in data
    # Basic sanity checks on the metric structure
    metrics = data["sample_cleaned.csv"]
    assert "t_test" in metrics
    assert "linear_regression" in metrics
    # Ensure numeric values are present
    assert isinstance(metrics["t_test"].get("p_value"), float)
    assert isinstance(metrics["linear_regression"].get("r_squared"), float)