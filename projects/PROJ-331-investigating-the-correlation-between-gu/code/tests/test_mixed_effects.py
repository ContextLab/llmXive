"""Unit tests for the mixed‑effects module (Task T005)."""

from __future__ import annotations

import pathlib
import tempfile

import numpy as np
import pandas as pd
import pytest

from code.src.pipeline import mixed_effects

@pytest.fixture
def synthetic_data(tmp_path: pathlib.Path):
    """Create a minimal synthetic dataset with a known interaction."""
    # Two patients, three visits each
    patients = ["p1", "p2"]
    dates = pd.date_range("2020-01-01", periods=3, freq="YS")
    rows = []
    for pid in patients:
        for i, date in enumerate(dates):
            # Simulate a taxon with a linear increase over time
            taxon_val = i * 0.5  # true slope = 0.5
            # Outcome generated with interaction: outcome = 10 + 2*time + 3*taxon + 4*time*taxon + noise
            time = i
            outcome = 10 + 2 * time + 3 * taxon_val + 4 * time * taxon_val + np.random.normal(
                0, 0.01
            )
            rows.append(
                {
                    "sample_id": f"{pid}_{i}",
                    "patient_id": pid,
                    "visit_date": date,
                    "taxon_x": taxon_val,
                    "age": 60,
                    "sex": "M",
                    "levodopa_eq_dose": 100,
                    "MDS_UPDRS_Total": outcome,
                }
            )
    df = pd.DataFrame(rows)
    # Write CLR parquet (here CLR is identity because values are already log‑transformed)
    clr_path = tmp_path / "clr_abundances.parquet"
    df_clr = df[
        ["sample_id", "patient_id", "visit_date", "taxon_x"]
    ].copy()
    df_clr.to_parquet(clr_path, index=False)

    # Write clinical parquet (contains outcome + covariates)
    clinical_path = tmp_path / "ppmi_clinical.parquet"
    df_clin = df[
        [
            "patient_id",
            "visit_date",
            "age",
            "sex",
            "levodopa_eq_dose",
            "MDS_UPDRS_Total",
        ]
    ].copy()
    df_clin.to_parquet(clinical_path, index=False)

    return clr_path, clinical_path, tmp_path

def test_mixed_effects_recovers_known_interaction(synthetic_data):
    clr_path, clinical_path, out_dir = synthetic_data
    out_path = out_dir / "mixed_effects_summary.csv"

    # Run the analysis
    mixed_effects.run_mixed_effects(clr_path, clinical_path, out_path)

    # Load results
    df_res = pd.read_csv(out_path)
    assert "taxon_x" in df_res["taxon_name"].values

    # Extract the row for our synthetic taxon
    row = df_res[df_res["taxon_name"] == "taxon_x"].iloc[0]

    # The true interaction coefficient is 4.0 (see data generation)
    # Allow a small tolerance due to numerical fitting.
    assert np.isclose(row["interaction_coef"], 4.0, atol=0.2)

    # p‑value should be very small (significant)
    assert row["raw_p"] < 0.01
    assert row["bh_adj_p"] < 0.01

def test_missing_outcome_causes_empty_file(synthetic_data):
    clr_path, clinical_path, out_dir = synthetic_data
    # Remove outcome column to trigger graceful skip
    clinical_df = pd.read_parquet(clinical_path)
    clinical_df = clinical_df.drop(columns=["MDS_UPDRS_Total"])
    clinical_no_outcome = out_dir / "no_outcome.parquet"
    clinical_df.to_parquet(clinical_no_outcome, index=False)

    out_path = out_dir / "mixed_effects_summary_missing.csv"
    mixed_effects.run_mixed_effects(clr_path, clinical_no_outcome, out_path)

    df_res = pd.read_csv(out_path)
    # Should contain only the header (no rows)
    assert df_res.empty
    assert list(df_res.columns) == [
        "taxon_name",
        "interaction_coef",
        "std_error",
        "raw_p",
        "bh_adj_p",
    ]