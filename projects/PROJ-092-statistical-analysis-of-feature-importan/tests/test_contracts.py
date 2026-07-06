"""
Unit tests for the data contract schemas.
"""
import pytest
from datetime import datetime
from contracts.dataset import DatasetSchema
from contracts.importance_profile import ImportanceProfileSchema
from contracts.drift_metric import DriftMetricSchema

def test_dataset_schema_validation():
    """Test that a valid dataset schema passes validation."""
    schema = DatasetSchema(
        window_id="W001",
        start_time=datetime(2023, 1, 1),
        end_time=datetime(2023, 1, 31),
        features=["load", "temp", "humidity"],
        target="load",
        row_count=1000,
        missing_value_count=0,
        dropped_features=[],
        variance_threshold=0.0
    )
    assert schema.validate() is True

def test_dataset_schema_missing_feature():
    """Test that a dataset schema with empty features fails validation."""
    schema = DatasetSchema(
        window_id="W002",
        start_time=datetime(2023, 2, 1),
        end_time=datetime(2023, 2, 28),
        features=[],
        target="load",
        row_count=1000,
        missing_value_count=0,
        dropped_features=[],
        variance_threshold=0.0
    )
    assert schema.validate() is False

def test_importance_profile_schema_valid():
    """Test that a valid importance profile passes validation."""
    profile = ImportanceProfileSchema(
        window_id="W001",
        model_type="RandomForestRegressor",
        r2_score=0.85,
        timestamp=datetime.now(),
        feature_importances={"load": 0.5, "temp": 0.5},
        permutation_scores={"load": 0.1, "temp": 0.2},
        permutation_stds={"load": 0.01, "temp": 0.02},
        is_valid=True
    )
    assert profile.validate() is True
    assert profile.to_dict()["is_valid"] is True

def test_importance_profile_schema_invalid_r2():
    """Test that a profile with negative R2 fails validation."""
    profile = ImportanceProfileSchema(
        window_id="W001",
        model_type="RandomForestRegressor",
        r2_score=-0.5,
        timestamp=datetime.now(),
        feature_importances={"load": 0.5},
        permutation_scores={"load": 0.1},
        permutation_stds={"load": 0.01},
        is_valid=True
    )
    assert profile.validate() is False

def test_drift_metric_schema_validation():
    """Test that a valid drift metric passes validation."""
    metric = DriftMetricSchema(
        window_t="W001",
        window_t_plus_1="W002",
        spearman_rho=0.8,
        p_value=0.01,
        is_significant=True,
        block_perm_p_value=0.04
    )
    assert metric.validate() is True

def test_drift_metric_schema_rho_out_of_range():
    """Test that a metric with rho > 1 fails validation."""
    metric = DriftMetricSchema(
        window_t="W001",
        window_t_plus_1="W002",
        spearman_rho=1.5,
        p_value=0.01,
        is_significant=True
    )
    assert metric.validate() is False

def test_drift_metric_schema_to_dict():
    """Test serialization of drift metric."""
    metric = DriftMetricSchema(
        window_t="W001",
        window_t_plus_1="W002",
        spearman_rho=0.5,
        p_value=0.05,
        is_significant=False
    )
    d = metric.to_dict()
    assert d["window_t"] == "W001"
    assert d["spearman_rho"] == 0.5
    assert "timestamp" in d
