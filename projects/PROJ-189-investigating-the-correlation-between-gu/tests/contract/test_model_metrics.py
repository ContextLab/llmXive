"""
Contract tests for model metrics schema (R², RMSE, VIF).

These tests verify that the model output artifacts produced by
code/04_predictive_modeling.py adhere to the expected schema.
"""
import json
import os
import pytest
from pathlib import Path
import numpy as np

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Expected output paths
MODEL_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "model_metrics.json"
COLLINEARITY_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "collinearity_review_log.json"
MODEL_SIGNIFICANCE_PATH = PROJECT_ROOT / "data" / "processed" / "model_significance.json"

def _load_json(path: Path) -> dict:
    """Load JSON file, raising FileNotFoundError if missing."""
    if not path.exists():
        pytest.fail(f"Expected output file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def _validate_scalar_metric(value, name: str, expected_type=(int, float)):
    """Assert a metric is a valid scalar number."""
    assert isinstance(value, expected_type), f"{name} must be a scalar number, got {type(value)}"
    assert not np.isnan(value), f"{name} cannot be NaN"
    assert not np.isinf(value), f"{name} cannot be infinite"

def _validate_vif_record(record: dict, taxon_name: str):
    """Validate a single VIF record structure."""
    assert "taxon" in record, f"Missing 'taxon' key in VIF record"
    assert record["taxon"] == taxon_name, f"Taxon name mismatch: expected {taxon_name}, got {record['taxon']}"
    assert "vif_score" in record, f"Missing 'vif_score' in VIF record"
    assert "flagged" in record, f"Missing 'flagged' boolean in VIF record"

    _validate_scalar_metric(record["vif_score"], "vif_score")
    assert isinstance(record["flagged"], bool), "flagged must be a boolean"

class TestModelMetricsSchema:
    """Contract tests for R², RMSE, and VIF output schemas."""

    def test_model_metrics_file_exists(self):
        """Verify model_metrics.json exists after pipeline execution."""
        assert MODEL_METRICS_PATH.exists(), "Model metrics output file not found"

    def test_model_metrics_schema_structure(self):
        """Verify model_metrics.json contains required top-level keys."""
        data = _load_json(MODEL_METRICS_PATH)

        required_keys = {"r2_score", "rmse", "mean_cv_r2", "std_cv_r2"}
        missing_keys = required_keys - set(data.keys())
        assert not missing_keys, f"Missing required keys in model_metrics.json: {missing_keys}"

    def test_model_metrics_r2_is_scalar(self):
        """Verify R² score is a valid scalar number."""
        data = _load_json(MODEL_METRICS_PATH)
        _validate_scalar_metric(data["r2_score"], "r2_score")

    def test_model_metrics_rmse_is_scalar(self):
        """Verify RMSE is a valid scalar number."""
        data = _load_json(MODEL_METRICS_PATH)
        _validate_scalar_metric(data["rmse"], "rmse")

    def test_model_metrics_cv_stats_are_scalar(self):
        """Verify cross-validation statistics are valid scalars."""
        data = _load_json(MODEL_METRICS_PATH)
        _validate_scalar_metric(data["mean_cv_r2"], "mean_cv_r2")
        _validate_scalar_metric(data["std_cv_r2"], "std_cv_r2")

class TestCollinearityLogSchema:
    """Contract tests for VIF collinearity review log."""

    def test_collinearity_log_file_exists(self):
        """Verify collinearity_review_log.json exists."""
        assert COLLINEARITY_LOG_PATH.exists(), "Collinearity log file not found"

    def test_collinearity_log_schema_structure(self):
        """Verify collinearity_review_log.json structure."""
        data = _load_json(COLLINEARITY_LOG_PATH)

        # Should be a list of records
        assert isinstance(data, list), "collinearity_review_log.json must be a list of records"
        assert len(data) > 0, "collinearity_review_log.json must contain at least one record"

        for record in data:
            assert isinstance(record, dict), "Each record must be a dictionary"
            assert "taxon" in record, "Each record must have 'taxon'"
            assert "vif_score" in record, "Each record must have 'vif_score'"
            assert "flagged" in record, "Each record must have 'flagged'"

    def test_collinearity_log_vif_values_valid(self):
        """Verify VIF scores are valid numbers and flags are booleans."""
        data = _load_json(COLLINEARITY_LOG_PATH)

        for record in data:
            _validate_scalar_metric(record["vif_score"], "vif_score")
            assert isinstance(record["flagged"], bool), "flagged must be boolean"
            # Consistency check: flagged should be True if vif > 5
            if record["vif_score"] > 5.0:
                assert record["flagged"] is True, "Taxon with VIF > 5.0 must be flagged"
            else:
                assert record["flagged"] is False, "Taxon with VIF <= 5.0 must not be flagged"

class TestModelSignificanceSchema:
    """Contract tests for model significance comparison against null threshold."""

    def test_model_significance_file_exists(self):
        """Verify model_significance.json exists."""
        assert MODEL_SIGNIFICANCE_PATH.exists(), "Model significance file not found"

    def test_model_significance_schema_structure(self):
        """Verify model_significance.json contains required keys."""
        data = _load_json(MODEL_SIGNIFICANCE_PATH)

        required_keys = {"observed_r2", "null_threshold_95th", "is_significant", "p_value_approx"}
        missing_keys = required_keys - set(data.keys())
        assert not missing_keys, f"Missing required keys in model_significance.json: {missing_keys}"

    def test_model_significance_values_valid(self):
        """Verify significance metrics are valid numbers and booleans."""
        data = _load_json(MODEL_SIGNIFICANCE_PATH)

        _validate_scalar_metric(data["observed_r2"], "observed_r2")
        _validate_scalar_metric(data["null_threshold_95th"], "null_threshold_95th")
        _validate_scalar_metric(data["p_value_approx"], "p_value_approx")

        assert isinstance(data["is_significant"], bool), "is_significant must be boolean"

        # Logical consistency check
        if data["observed_r2"] > data["null_threshold_95th"]:
            assert data["is_significant"] is True, "Model is significant if observed > threshold"
        else:
            assert data["is_significant"] is False, "Model is not significant if observed <= threshold"