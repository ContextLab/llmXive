"""
Unit tests for the metabolic syndrome classifier (T014).

These tests use a tiny synthetic phenotype DataFrame constructed on‑the‑fly.
The classifier itself reads the phenotype from the loader; therefore we patch
``load_gtex_phenotype_data`` and ``verify_clinical_columns`` to return the
synthetic data.
"""

import builtins
import io
import json
import types
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from code.data.classifier import classify_metabolic_status

# -------------------------------------------------------------------------
# Helper – a minimal synthetic phenotype DataFrame
# -------------------------------------------------------------------------
def _make_synthetic_phenotype():
    """Return a DataFrame with the exact columns required by the classifier."""
    data = {
        "sample_id": ["S1", "S2", "S3", "S4"],
        "bmi": [32.0, 28.0, 31.0, 29.5],
        "fasting_glucose": [110.0, 95.0, 105.0, 99.0],
        "triglycerides": [160.0, 140.0, 155.0, 145.0],
        "hdl": [45.0, 55.0, 48.0, 52.0],
        "systolic_bp": [135.0, 120.0, 128.0, 132.0],
        "diastolic_bp": [88.0, 78.0, 84.0, 86.0],
    }
    return pd.DataFrame(data)

# -------------------------------------------------------------------------
# Fixtures – monkey‑patch the loader utilities
# -------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def patch_loader(monkeypatch):
    """Replace the real loader functions with stubs returning synthetic data."""
    from code.data import loader as loader_module

    # Stub that returns our synthetic DataFrame
    def fake_load():
        return _make_synthetic_phenotype()

    # Stub that pretends all required columns are present
    def fake_verify(df, required):
        return []  # no missing columns

    monkeypatch.setattr(loader_module, "load_gtex_phenotype_data", fake_load)
    monkeypatch.setattr(loader_module, "verify_clinical_columns", fake_verify)

# -------------------------------------------------------------------------
# Test – correct classification according to ATP‑III (≥3 criteria => MetS)
# -------------------------------------------------------------------------
def test_atp_iii_classifies_metabolic_syndrome(tmp_path, monkeypatch):
    """
    Verify that donors meeting three or more criteria are labelled “MetS” and
    others are labelled “Control”.
    """
    # Run the classifier
    classify_metabolic_status()

    # Load the produced baseline labels
    labels_path = Path("data/processed/baseline_labels.csv")
    df = pd.read_csv(labels_path)

    # Expected labels based on the synthetic data above:
    # S1 meets BMI, Glucose, TG, BP (4) -> MetS
    # S2 meets none (0) -> Control
    # S3 meets BMI, Glucose, TG (3) -> MetS
    # S4 meets BMI, BP (2) -> Control
    expected = {
        "S1": ("MetS", 4),
        "S2": ("Control", 0),
        "S3": ("MetS", 3),
        "S4": ("Control", 2),
    }

    for _, row in df.iterrows():
        sid = row["sample_id"]
        exp_label, exp_count = expected[sid]
        assert row["label"] == exp_label
        assert row["criteria_count"] == exp_count

# -------------------------------------------------------------------------
# Test – samples with missing data are excluded from both outputs
# -------------------------------------------------------------------------
def test_excludes_missing_data(monkeypatch):
    """If any required column is NaN, the sample must not appear in outputs."""
    # Create a phenotype where the second sample lacks HDL
    df = _make_synthetic_phenotype()
    df.loc[1, "hdl"] = float("nan")  # introduce missing value

    # Patch loader to return this modified frame
    from code.data import loader as loader_module

    monkeypatch.setattr(loader_module, "load_gtex_phenotype_data", lambda: df)
    monkeypatch.setattr(
        loader_module, "verify_clinical_columns", lambda d, r: []
    )

    classify_metabolic_status()

    # The excluded sample (S2) should be absent from both files
    baseline = pd.read_csv(Path("data/processed/baseline_labels.csv"))
    filtered = pd.read_csv(Path("data/processed/filtered_phenotype.csv"))

    assert "S2" not in baseline["sample_id"].values
    assert "S2" not in filtered["sample_id"].values

# -------------------------------------------------------------------------
# Test – boundary conditions (strict thresholds)
# -------------------------------------------------------------------------
def test_boundary_conditions(monkeypatch):
    """
    Verify that values exactly on the threshold are considered meeting the
    criterion (e.g., BMI == 30, HDL == 50 is NOT a risk because HDL uses '<').
    """
    df = pd.DataFrame(
        {
            "sample_id": ["B1", "H1"],
            "bmi": [30.0, 29.9],  # exactly at threshold -> meets
            "fasting_glucose": [100.0, 99.9],
            "triglycerides": [150.0, 149.9],
            "hdl": [50.0, 50.1],  # 50.0 is NOT below threshold, 50.1 also not
            "systolic_bp": [130.0, 129.9],
            "diastolic_bp": [85.0, 84.9],
        }
    )

    from code.data import loader as loader_module

    monkeypatch.setattr(loader_module, "load_gtex_phenotype_data", lambda: df)
    monkeypatch.setattr(
        loader_module, "verify_clinical_columns", lambda d, r: []
    )

    classify_metabolic_status()

    baseline = pd.read_csv(Path("data/processed/baseline_labels.csv"))
    # B1 meets all 5 criteria (BMI, Glucose, TG, BP systolic, BP diastolic) -> MetS
    # H1 meets none -> Control
    label_map = dict(zip(baseline["sample_id"], baseline["label"]))
    assert label_map["B1"] == "MetS"
    assert label_map["H1"] == "Control"
