"""
Basic sanity test for the feature engineering script.

The test checks that the script runs without error on a minimal
handcrafted CSV containing a single, well‑known perovskite formula.
It validates that the output file exists and that a few expected
descriptor columns are present.
"""

import csv
import os
from pathlib import Path

import pandas as pd
import pytest

# Import the main function from the module we just implemented.
from code.feature_engineering import main as feature_engineering_main

@pytest.fixture
def minimal_raw_csv(tmp_path: Path):
    """Create a minimal raw CSV with one perovskite entry."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / "nrel_perovskites.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["formula", "T_d"])
        # Cesium lead bromide – a simple perovskite.
        writer.writerow(["CsPbBr3", 550])
    return csv_path

def test_feature_engineering_produces_output(minimal_raw_csv, tmp_path):
    """
    Run the feature engineering script and verify the output.
    """
    # Ensure any previous output is removed.
    output_path = Path("data/processed/descriptors.csv")
    if output_path.is_file():
        output_path.unlink()

    # Execute the script.
    feature_engineering_main()

    # Verify the output file exists.
    assert output_path.is_file(), "Descriptor CSV was not created."

    # Load the output and perform a few sanity checks.
    df = pd.read_csv(output_path)
    # Should contain exactly one row (the one we supplied).
    assert len(df) == 1, "Unexpected number of rows in descriptor output."

    # Check that expected columns are present.
    expected_cols = {
        "formula",
        "T_d",
        "atomic_fraction_Cs",
        "atomic_fraction_Pb",
        "atomic_fraction_Br",
        "weighted_ionic_radius",
        "weighted_electronegativity",
        "weighted_formation_enthalpy",
        "weighted_first_ionization_energy",
        "variance_ionic_radius",
    }
    missing = expected_cols - set(df.columns)
    assert not missing, f"Missing expected descriptor columns: {missing}"