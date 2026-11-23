"""
test_preprocess.py
-------------------
Unit tests for the preprocessing pipeline defined in
``code/src/preprocess.py``.
"""

import json
import os

import numpy as np
import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the function under test
from code.src.preprocess import load_and_preprocess

@pytest.fixture
def raw_dataframes():
    """Create two small raw DataFrames with heterogeneous column names."""
    df1 = pd.DataFrame(
        {
            "species_id": [1, 2, 3],
            "family": ["FamA", "FamB", "FamA"],
            "Alkaloid_conc": [0.5, 0.7, np.nan],
            "terpenes": [1.2, 0.8, 1.0],
            "Phenolics": [0.3, 0.4, 0.5],
            "benzoxazinoids": [0.0, 0.1, 0.2],
            "herbivory_score": [10, 20, 30],
        }
    )
    # Second dataframe missing the 'benzoxazinoids' column entirely – this
    # should be treated as documented absence and imputed with zeros.
    df2 = pd.DataFrame(
        {
            "species_id": [4, 5],
            "family": ["FamB", "FamC"],
            "Alkaloid_conc": [0.6, 0.9],
            "Terpenes": [1.1, 1.3],
            "Phenolics": [0.35, 0.45],
            # No benzoxazinoids column
            "herbivory_score": [15, 25],
        }
    )
    return [df1, df2]

def _is_absent(indicator_json: str, metabolite: str) -> bool:
    """Return True if the given metabolite is recorded as absent in the JSON indicator."""
    try:
        indicator = json.loads(indicator_json)
    except json.JSONDecodeError:
        return False
    return metabolite in indicator

def test_load_and_preprocess_basic(raw_dataframes):
    """Basic sanity checks after running the preprocessing pipeline."""
    cleaned_df = load_and_preprocess(raw_dataframes)

    # 1. No missing values in required columns
    required = [
        "species_id",
        "family",
        "alkaloids",
        "terpenes",
        "phenolics",
        "benzoxazinoids",
        "herbivory_score",
    ]
    assert not cleaned_df[required].isnull().any().any(), "Missing values remain after preprocessing"

    # 2. For rows where a metabolite class was documented as absent,
    #    the standardized value must be exactly zero.
    for met in ["alkaloids", "terpenes", "phenolics", "benzoxazinoids"]:
        absent_mask = cleaned_df["absence_indicator"].apply(lambda x: _is_absent(x, met))
        # Values in absent rows should be zero
        assert (cleaned_df.loc[absent_mask, met] == 0.0).all(), f"{met} not zero for documented absent rows"

        # For rows where the metabolite is *present*, the Z‑scored values
        # should have mean ≈ 0 and std ≈ 1 (population std).
        present_mask = ~absent_mask
        present_vals = cleaned_df.loc[present_mask, met]
        if not present_vals.empty:
            mean = present_vals.mean()
            std = present_vals.std(ddof=0)
            assert abs(mean) < 1e-6, f"{met} mean not close to 0 (got {mean})"
            assert abs(std - 1.0) < 1e-6, f"{met} std not close to 1 (got {std})"

    # 3. absence_indicator column exists and is valid JSON
    assert "absence_indicator" in cleaned_df.columns
    # Parse a few rows to ensure JSON loads
    for val in cleaned_df["absence_indicator"].head():
        parsed = json.loads(val)
        assert isinstance(parsed, dict)

    # 4. Output file exists and checksum log is present
    clean_path = paths.data("processed", "clean.parquet")
    assert clean_path.is_file(), f"Clean parquet not written at {clean_path}"
    log_path = paths.outputs("preprocessing_log.json")
    assert log_path.is_file(), f"Preprocessing log not written at {log_path}"
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = json.load(f)
    assert "checksum_sha256" in log_content, "Checksum missing in preprocessing log"

def test_missing_required_rows_are_dropped():
    """Rows with any required NaN should be removed."""
    df = pd.DataFrame(
        {
            "species_id": [1, 2],
            "family": ["FamA", "FamB"],
            "Alkaloid_conc": [0.5, np.nan],  # second row missing alkaloid
            "terpenes": [1.0, 1.2],
            "Phenolics": [0.3, 0.4],
            "benzoxazinoids": [0.0, 0.1],
            "herbivory_score": [10, 20],
        }
    )
    cleaned = load_and_preprocess([df])
    # Only the first row should survive
    assert cleaned.shape[0] == 1
    assert cleaned.iloc[0]["species_id"] == 1

def test_outlier_capping():
    """Extreme herbivory scores should be capped at the upper whisker."""
    # Construct data with a clear high outlier
    df = pd.DataFrame(
        {
            "species_id": [1, 2, 3],
            "family": ["FamA", "FamA", "FamA"],
            "Alkaloid_conc": [0.5, 0.6, 0.7],
            "terpenes": [1.0, 1.1, 1.2],
            "Phenolics": [0.3, 0.35, 0.4],
            "benzoxazinoids": [0.0, 0.1, 0.2],
            "herbivory_score": [10, 12, 1000],  # 1000 is an outlier
        }
    )
    cleaned = load_and_preprocess([df])
    # Compute the upper whisker from the original raw data
    raw_scores = df["herbivory_score"]
    q1 = raw_scores.quantile(0.25)
    q3 = raw_scores.quantile(0.75)
    iqr = q3 - q1
    upper_whisker = q3 + 1.5 * iqr
    capped_val = cleaned["herbivory_score"].iloc[2]
    assert capped_val == upper_whisker, "Outlier was not capped correctly"