"""
Contract test for data schema validation (US1).

This test verifies that the derived trial data produced by data/preprocess.py
strictly adheres to the required schema for User Story 1 analysis.

Required columns:
- participant_id
- trial_id
- stimulus_modality
- source_label
- participant_response
- confidence_rating

It also validates data types and enumerations (e.g., valid modalities).
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path

# Ensure project root is in path for imports if running from tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
TRIAL_DATA_PATH = DERIVED_DIR / "trial_data.csv"
VALIDATION_REPORT_PATH = DATA_DIR / "validation_report.json"

# Expected schema definition
REQUIRED_COLUMNS = [
    "participant_id",
    "trial_id",
    "stimulus_modality",
    "source_label",
    "participant_response",
    "confidence_rating"
]

VALID_MODALITIES = {"visual", "auditory"}
VALID_SOURCE_LABELS = {"internal", "external"}

class TestDataSchemaContract:
    """
    Contract tests ensuring the trial_data.csv meets the strict schema
    required for the Hold-Out Accuracy analysis in User Story 1.
    """

    @pytest.fixture(scope="class")
    def trial_data(self):
        """Load the trial data if it exists, otherwise skip."""
        if not TRIAL_DATA_PATH.exists():
            pytest.skip(f"Derived data file not found: {TRIAL_DATA_PATH}. "
                        "Run data/preprocess.py (T012) first.")
        try:
            return pd.read_csv(TRIAL_DATA_PATH)
        except Exception as e:
            pytest.fail(f"Failed to load {TRIAL_DATA_PATH}: {e}")

    @pytest.fixture(scope="class")
    def validation_report(self):
        """Load the validation report from T006 if it exists."""
        if not VALIDATION_REPORT_PATH.exists():
            return None
        try:
            with open(VALIDATION_REPORT_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def test_file_exists(self):
        """Contract: The derived trial data file must exist."""
        assert TRIAL_DATA_PATH.exists(), (
            f"Contract violation: {TRIAL_DATA_PATH} does not exist. "
            "Ensure T012 (preprocess.py) has been executed."
        )

    def test_required_columns_present(self, trial_data):
        """Contract: All required columns must be present in the DataFrame."""
        missing = set(REQUIRED_COLUMNS) - set(trial_data.columns)
        assert not missing, (
            f"Contract violation: Missing required columns: {missing}. "
            f"Found columns: {list(trial_data.columns)}"
        )

    def test_column_types_numeric(self, trial_data):
        """Contract: Numeric columns must be numeric."""
        numeric_cols = ["confidence_rating", "participant_response"]
        for col in numeric_cols:
            if col in trial_data.columns:
                # Allow object dtype if it can be coerced, but strict contract prefers numeric
                assert pd.api.types.is_numeric_dtype(trial_data[col]) or \
                       pd.api.types.is_integer_dtype(trial_data[col]) or \
                       pd.api.types.is_float_dtype(trial_data[col]), \
                       f"Contract violation: Column '{col}' is not numeric."

    def test_stimulus_modality_values(self, trial_data):
        """Contract: stimulus_modality must be one of the valid enumerations."""
        if "stimulus_modality" in trial_data.columns:
            unique_modalities = set(trial_data["stimulus_modality"].dropna().unique())
            invalid = unique_modalities - VALID_MODALITIES
            assert not invalid, (
                f"Contract violation: Invalid stimulus_modality values found: {invalid}. "
                f"Allowed values: {VALID_MODALITIES}"
            )

    def test_source_label_values(self, trial_data):
        """Contract: source_label must be one of the valid enumerations."""
        if "source_label" in trial_data.columns:
            unique_labels = set(trial_data["source_label"].dropna().unique())
            invalid = unique_labels - VALID_SOURCE_LABELS
            assert not invalid, (
                f"Contract violation: Invalid source_label values found: {invalid}. "
                f"Allowed values: {VALID_SOURCE_LABELS}"
            )

    def test_no_nulls_in_critical_fields(self, trial_data):
        """Contract: Critical analysis fields must not contain nulls."""
        critical_fields = ["participant_id", "trial_id", "source_label", "confidence_rating"]
        for field in critical_fields:
            if field in trial_data.columns:
                null_count = trial_data[field].isnull().sum()
                assert null_count == 0, (
                    f"Contract violation: Column '{field}' contains {null_count} null values. "
                    "Critical fields must be non-null."
                )

    def test_validation_report_status(self, validation_report):
        """Contract: The upstream validation report (T006) must indicate PASS."""
        if validation_report is None:
            pytest.skip("Validation report (T006) not found. Skipping upstream check.")
        
        assert validation_report.get("status") == "PASS", (
            f"Contract violation: Upstream validation report status is '{validation_report.get('status')}'. "
            "T006 must pass before T010 can validate the derived schema."
        )

    def test_trial_id_uniqueness(self, trial_data):
        """Contract: trial_id must be unique within the dataset."""
        if "trial_id" in trial_data.columns:
            assert trial_data["trial_id"].is_unique, (
                "Contract violation: trial_id values are not unique. "
                "Each trial must have a unique identifier."
            )