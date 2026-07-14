"""
Unit test for the outlier threshold sweep implementation (Task T033).

The test creates a tiny synthetic dataset, writes it to ``data/raw``,
runs the sweep with a single ``k`` value, and checks that the output JSON
is created and contains the expected keys.
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from t033_outlier_threshold_sweep import outlier_threshold_sweep, main

@pytest.fixture(scope="module")
def synthetic_raw_dataset(tmp_path_factory):
    """Create a minimal CSV file in data/raw for the test."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            "feature1": [1, 2, 100, 4, 5],  # contains an outlier at 100
            "feature2": [5, 4, 3, 2, 1],
            "outcome": [0, 1, 0, 1, 0],
        }
    )
    csv_path = raw_dir / "synthetic.csv"
    df.to_csv(csv_path, index=False)
    yield csv_path
    # Cleanup after the module
    if csv_path.exists():
        csv_path.unlink()

def test_outlier_threshold_sweep_produces_output(tmp_path):
    # Ensure a clean output directory
    output_path = Path("data/processed/outlier_threshold_sweep.json")
    if output_path.exists():
        output_path.unlink()

    # Run the sweep with a deterministic k value
    results = outlier_threshold_sweep([1.5])
    assert isinstance(results, dict)
    assert 1.5 in results
    assert "fpr" in results[1.5]
    assert "inconsistency_rate" in results[1.5]

    # Run the CLI main() which writes the file
    main()
    assert output_path.is_file()

    # Verify JSON structure
    with open(output_path, "r") as f:
        data = json.load(f)
    assert "1.5" in data or 1.5 in data  # JSON may stringify keys
    assert isinstance(data[str(1.5)], dict)
    assert "fpr" in data[str(1.5)]
    assert "inconsistency_rate" in data[str(1.5)]

# The test suite can be executed with: ``pytest -q tests/test_outlier_threshold_sweep.py``