"""
Unit test for the KS uniformity test implementation.

The test creates a tiny temporary CSV containing a column ``p_value``
with values drawn from a uniform distribution, runs the ``uniformity_test``
script, and checks that the output JSON file is created and contains
the expected keys with numeric values.
"""

from pathlib import Path
import json

import pandas as pd
import numpy as np
import pytest

# Import the module under test
from code.uniformity_test import main as uniformity_main, INPUT_CSV, OUTPUT_JSON

@pytest.fixture
def temp_csv(tmp_path: Path):
    """Create a temporary ``autocorr_stats.csv`` with uniform p-values."""
    csv_path = tmp_path / "autocorr_stats.csv"
    # Generate 100 uniform p-values
    pvals = np.random.rand(100)
    df = pd.DataFrame({"p_value": pvals})
    df.to_csv(csv_path, index=False)
    return csv_path

def test_ks_uniformity_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, temp_csv: Path):
    # Redirect the input and output paths to the temporary directory
    monkeypatch.setattr("code.uniformity_test.INPUT_CSV", temp_csv)
    output_path = tmp_path / "uniformity_test.json"
    monkeypatch.setattr("code.uniformity_test.OUTPUT_JSON", output_path)

    # Run the script
    uniformity_main()

    # Verify output file exists
    assert output_path.is_file(), "Output JSON file was not created."

    # Verify JSON structure
    with output_path.open() as f:
        data = json.load(f)

    assert "ks_statistic" in data and "p_value" in data, "Missing keys in output JSON."
    assert isinstance(data["ks_statistic"], float), "ks_statistic should be a float."
    assert isinstance(data["p_value"], float), "p_value should be a float."
    # The KS p‑value for a truly uniform sample should not be extremely small
    assert data["p_value"] > 0.01, "KS test unexpectedly indicates non‑uniformity."