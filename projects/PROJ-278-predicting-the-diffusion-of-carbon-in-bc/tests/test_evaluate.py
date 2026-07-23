"""
Test suite for User Story 3: Evaluate model performance, SHAP analysis, and variance partitioning.
Verifies artifacts produced by code/04_evaluate.py.
"""

import os
import json
import pytest
import pandas as pd
from pathlib import Path

# Project root relative to test execution (assuming tests/ is at root)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_OUTPUTS = PROJECT_ROOT / "data" / "outputs"

# Expected artifact paths
FEATURE_IMPORTANCE_PATH = DATA_OUTPUTS / "feature_importance.json"
VARIANCE_PARTITION_PATH = DATA_OUTPUTS / "variance_partition.csv"
PDP_DIR = DATA_OUTPUTS / "partial_dependence_plots"

# Ensure output directory exists for tests (in case scripts haven't run yet)
# The tests themselves verify existence, but we need to handle the case where the directory is missing
# to provide a clear error message rather than a FileNotFoundError on os.listdir.
if not DATA_OUTPUTS.exists():
    DATA_OUTPUTS.mkdir(parents=True, exist_ok=True)
if not PDP_DIR.exists():
    PDP_DIR.mkdir(parents=True, exist_ok=True)


class TestEvaluateArtifacts:
    """Tests to verify the existence and validity of evaluation artifacts."""

    def test_feature_importance_json_exists(self):
        """Verify that feature_importance.json is generated."""
        assert FEATURE_IMPORTANCE_PATH.exists(), f"Expected file {FEATURE_IMPORTANCE_PATH} not found. Run code/04_evaluate.py first."

    def test_feature_importance_json_valid_structure(self):
        """Verify feature_importance.json contains required keys and valid data."""
        if not FEATURE_IMPORTANCE_PATH.exists():
            pytest.skip("Feature importance file not generated yet.")

        with open(FEATURE_IMPORTANCE_PATH, 'r') as f:
            data = json.load(f)

        # Check required keys based on T019/T005 spec
        required_keys = ["ranked_features", "top_two"]
        for key in required_keys:
            assert key in data, f"Missing required key '{key}' in feature_importance.json"

        # Verify ranked_features is a list of strings
        assert isinstance(data["ranked_features"], list), "ranked_features must be a list"
        assert len(data["ranked_features"]) > 0, "ranked_features cannot be empty"
        assert all(isinstance(item, str) for item in data["ranked_features"]), "All items in ranked_features must be strings"

        # Verify top_two is a list of exactly two strings
        assert isinstance(data["top_two"], list), "top_two must be a list"
        assert len(data["top_two"]) == 2, f"top_two must contain exactly 2 items, found {len(data['top_two'])}"
        assert all(isinstance(item, str) for item in data["top_two"]), "All items in top_two must be strings"

    def test_variance_partition_csv_exists(self):
        """Verify that variance_partition.csv is generated."""
        assert VARIANCE_PARTITION_PATH.exists(), f"Expected file {VARIANCE_PARTITION_PATH} not found. Run code/04_evaluate.py first."

    def test_variance_partition_csv_valid_structure(self):
        """Verify variance_partition.csv contains required columns and valid data."""
        if not VARIANCE_PARTITION_PATH.exists():
            pytest.skip("Variance partition file not generated yet.")

        df = pd.read_csv(VARIANCE_PARTITION_PATH)

        # Check required columns based on T005 spec and T019 implementation
        required_columns = ["adjusted_r2", "microstructural_gap", "residual_variance_label"]
        for col in required_columns:
            assert col in df.columns, f"Missing required column '{col}' in variance_partition.csv"

        # Verify data types and values
        assert len(df) > 0, "variance_partition.csv is empty"

        # Check adjusted_r2 is numeric
        assert pd.api.types.is_numeric_dtype(df["adjusted_r2"]), "adjusted_r2 must be numeric"
        adjusted_r2 = df.iloc[0]["adjusted_r2"]
        assert -1.0 <= adjusted_r2 <= 1.0, f"adjusted_r2 ({adjusted_r2}) must be between -1 and 1"

        # Check microstructural_gap is numeric and consistent with adjusted_r2
        assert pd.api.types.is_numeric_dtype(df["microstructural_gap"]), "microstructural_gap must be numeric"
        microstructural_gap = df.iloc[0]["microstructural_gap"]
        # Allow for floating point precision errors
        expected_gap = 1.0 - adjusted_r2
        assert abs(microstructural_gap - expected_gap) < 1e-6, \
            f"microstructural_gap ({microstructural_gap}) does not match 1 - adjusted_r2 ({expected_gap})"

        # Check residual_variance_label is a string and contains expected keywords
        assert df["residual_variance_label"].dtype == object, "residual_variance_label must be a string"
        label = df.iloc[0]["residual_variance_label"]
        assert isinstance(label, str), "residual_variance_label must be a string"
        # Per T019, label should mention noise, measurement error, or missing descriptors
        lower_label = label.lower()
        assert ("noise" in lower_label or "measurement" in lower_label or "missing" in lower_label or "descriptor" in lower_label), \
            f"residual_variance_label '{label}' should describe noise, measurement error, or missing descriptors"

    def test_partial_dependence_plots_exist(self):
        """Verify that partial dependence plots are saved to data/outputs/."""
        # T019 specifies saving plots to data/outputs/
        # We check for the existence of plot files (e.g., .png) in the outputs directory or a subdirectory
        plot_files = list(DATA_OUTPUTS.glob("*.png"))
        # Also check the specific PDP directory if created by 04_evaluate.py
        pdp_files = list(PDP_DIR.glob("*.png"))

        # The task requires plots to be saved. If 04_evaluate.py creates them in a subdirectory, check that.
        # If it saves directly to outputs, check that.
        # We expect at least one plot file to exist if the evaluation script ran successfully.
        # However, if the script hasn't run, we skip to avoid false negatives in CI setup.
        # But per T027 requirement: "Plot files exist and contain valid data."
        # We assume 04_evaluate.py has been run before these tests in the pipeline.

        if not plot_files and not pdp_files:
            # If no plots found, check if the evaluation script was actually run
            # by checking for the existence of the main output files
            if not FEATURE_IMPORTANCE_PATH.exists() or not VARIANCE_PARTITION_PATH.exists():
                pytest.skip("Evaluation artifacts not generated. Run code/04_evaluate.py first.")
            else:
                # Main artifacts exist but plots don't - this is a failure of 04_evaluate.py
                pytest.fail("Partial dependence plots not found in data/outputs/ or data/outputs/partial_dependence_plots/. "
                            "code/04_evaluate.py must save PDPs to data/outputs/.")

        # If we have plots, verify they are non-empty
        plot_paths = plot_files + pdp_files
        for p in plot_paths:
            assert p.stat().st_size > 0, f"Plot file {p} is empty"

    def test_feature_importance_top_two_in_ranked(self):
        """Verify that the top two features are included in the ranked list."""
        if not FEATURE_IMPORTANCE_PATH.exists():
            pytest.skip("Feature importance file not generated yet.")

        with open(FEATURE_IMPORTANCE_PATH, 'r') as f:
            data = json.load(f)

        ranked = set(data["ranked_features"])
        top_two = set(data["top_two"])

        assert top_two.issubset(ranked), \
            f"top_two features {top_two} must be a subset of ranked_features {ranked}"

    def test_variance_partition_consistency(self):
        """Verify that variance partitioning metrics are logically consistent."""
        if not VARIANCE_PARTITION_PATH.exists():
            pytest.skip("Variance partition file not generated yet.")

        df = pd.read_csv(VARIANCE_PARTITION_PATH)
        row = df.iloc[0]

        adjusted_r2 = row["adjusted_r2"]
        microstructural_gap = row["microstructural_gap"]

        # The sum of adjusted_r2 and microstructural_gap should be approximately 1.0
        # (assuming residual_variance_label represents the remaining unexplained variance)
        # Note: The spec says microstructural_gap = 1 - adjusted_r2.
        # The residual_variance_label is a string description, not a numeric value in the CSV.
        # So we just check the gap calculation.
        assert abs((adjusted_r2 + microstructural_gap) - 1.0) < 1e-6, \
            f"adjusted_r2 ({adjusted_r2}) + microstructural_gap ({microstructural_gap}) should equal 1.0"

        # Ensure adjusted_r2 is not NaN
        assert not pd.isna(adjusted_r2), "adjusted_r2 cannot be NaN"
        assert not pd.isna(microstructural_gap), "microstructural_gap cannot be NaN"