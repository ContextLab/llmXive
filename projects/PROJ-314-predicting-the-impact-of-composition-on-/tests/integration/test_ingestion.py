"""
Integration test for the full ingestion pipeline.

This test verifies that the ingestion functions can be chained together on a
small, in‑memory sample without raising errors and that the resulting DataFrame
conforms to the expected schema defined for the project.

The test uses ``pytest`` and monkeypatches ``fetch_data`` to return a minimal
handcrafted DataFrame so that the test does not depend on external network
resources or a fully‑implemented ``fetch_data`` function.
"""

import pandas as pd
import pytest

# Import the pipeline components
from ingestion import fetch_data, validate_data_gap, clean_data
from descriptors import compute_descriptors

# Expected columns after the full ingestion + descriptor computation step.
# The list mirrors the schema described in the project tasks (T018/T019).
EXPECTED_COLUMNS = [
    "composition",
    "weibull_modulus",
    "sample_count",
    "is_range_flag",
    "range_original",
    "range_uncertainty",
    "primary_anion_cation_group",
    "mean_atomic_radius",
    "electronegativity_std",
    "valence_electron_concentration",
    "cation_size_variance",
    "sintering_temp",
    "is_imputed",
]

# Primary predictor columns that must contain no missing values after the pipeline.
PRIMARY_PREDICTORS = [
    "mean_atomic_radius",
    "electronegativity_std",
    "valence_electron_concentration",
    "cation_size_variance",
    "sintering_temp",
]

def _sample_raw_dataframe() -> pd.DataFrame:
    """
    Construct a tiny, realistic sample DataFrame that mimics the shape of the
    raw ceramic data expected by the ingestion pipeline.

    The data uses real chemical formulas and plausible numeric values so
    that downstream descriptor calculations (e.g. via ``chemparse``) can run
    without artificial hacks.
    """
    data = {
        # Simple stoichiometric oxides – real compositions.
        "composition": ["Al2O3", "SiO2", "MgAl2O4"],
        # Weibull modulus values taken from literature examples (real numbers).
        "weibull_modulus": [12.5, 9.8, 14.2],
        # Sample size column – the pipeline looks for N, sample_size or n.
        "N": [45, 60, 38],
        # Optional processing temperature column.
        "sintering_temp": [1500, 1450, 1520],
        # Additional columns that may be present in raw data but are not required.
        "extra_info": ["foo", "bar", "baz"],
    }
    return pd.DataFrame(data)

def test_full_ingestion_pipeline(monkeypatch):
    """
    End‑to‑end test that runs the ingestion pipeline on the sample data.
    """
    # ------------------------------------------------------------------
    # Monkeypatch ``fetch_data`` so that it returns our handcrafted sample.
    # ------------------------------------------------------------------
    monkeypatch.setattr("ingestion.fetch_data", lambda: _sample_raw_dataframe())

    # ------------------------------------------------------------------
    # Run the pipeline steps.
    # ------------------------------------------------------------------
    raw_df = fetch_data()
    assert isinstance(raw_df, pd.DataFrame), "fetch_data should return a DataFrame"

    # ``validate_data_gap`` is expected to either return the DataFrame or raise
    # an exception if the data set is too small. Our sample contains >30 rows per
    # entry, so it should pass.
    df_after_gap = validate_data_gap(raw_df)

    # Clean the data (filtering, imputation, range handling, etc.).
    cleaned_df = clean_data(df_after_gap)

    # Compute the chemical descriptors.
    described_df = compute_descriptors(cleaned_df)

    # ------------------------------------------------------------------
    # Assertions on the final DataFrame.
    # ------------------------------------------------------------------
    # 1. All expected columns are present.
    for col in EXPECTED_COLUMNS:
        assert col in described_df.columns, f"Missing expected column: {col}"

    # 2. No missing values in primary predictor columns.
    missing_mask = described_df[PRIMARY_PREDICTORS].isnull()
    assert not missing_mask.any().any(), "Primary predictors contain missing values"

    # 3. The number of rows should match the original sample size.
    assert len(described_df) == len(raw_df), "Row count changed unexpectedly"

    # 4. Basic sanity checks on numeric ranges.
    assert described_df["weibull_modulus"].min() > 0, "Weibull modulus should be positive"
    assert described_df["sintering_temp"].min() > 0, "Sintering temperature should be positive"

    # If we reach this point the full ingestion pipeline works on the sample.