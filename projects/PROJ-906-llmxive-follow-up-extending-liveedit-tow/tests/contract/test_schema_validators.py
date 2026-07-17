"""
Contract tests for T007: Schema Validators.
Verifies that Dataset, Metric, and Analysis schemas correctly validate JSON records
and raise errors on mismatch.
"""
import json
import pytest
from datetime import datetime
from pydantic import ValidationError

from contracts.dataset_schema import DatasetValidator, VideoClipSchema
from contracts.metric_schema import MetricValidator, MetricRecordSchema
from contracts.analysis_schema import AnalysisValidator, StatisticalTestResult


# --- Dataset Schema Tests ---

def test_valid_dataset_schema():
    """Test that a valid dataset JSON record passes validation."""
    valid_data = {
        "dataset_id": "test-ds-001",
        "name": "Test Dataset",
        "created_at": datetime.utcnow().isoformat(),
        "clips": [
            {
                "clip_id": "clip-001",
                "source_dataset": "DAVIS",
                "duration_seconds": 10.5,
                "frame_count": 315,
                "resolution": [480, 640],
                "fps": 30.0,
                "motion_magnitude": 0.45,
                "stratification_group": "low"
            }
        ],
        "total_clips": 1,
        "metadata": {"source": "manual"}
    }
    # Should not raise
    result = DatasetValidator.validate_from_dict(valid_data)
    assert result.dataset_id == "test-ds-001"
    assert len(result.clips) == 1
    assert result.clips[0].clip_id == "clip-001"


def test_invalid_dataset_schema_missing_field():
    """Test that missing required fields raise ValidationError."""
    invalid_data = {
        "dataset_id": "test-ds-002",
        "name": "Incomplete Dataset",
        # Missing 'clips' and 'total_clips'
        "created_at": datetime.utcnow().isoformat(),
        "total_clips": 0
    }
    with pytest.raises(ValidationError):
        DatasetValidator.validate_from_dict(invalid_data)


def test_invalid_dataset_schema_total_mismatch():
    """Test that mismatched total_clips raises ValidationError."""
    invalid_data = {
        "dataset_id": "test-ds-003",
        "name": "Mismatched Dataset",
        "created_at": datetime.utcnow().isoformat(),
        "clips": [
            {
                "clip_id": "c1", "source_dataset": "DAVIS", "duration_seconds": 1.0,
                "frame_count": 30, "resolution": [480, 640], "fps": 30.0
            }
        ],
        "total_clips": 5, # Claims 5, but only 1 clip provided
        "metadata": {}
    }
    with pytest.raises(ValidationError) as exc_info:
        DatasetValidator.validate_from_dict(invalid_data)
    assert "total_clips" in str(exc_info.value).lower()


# --- Metric Schema Tests ---

def test_valid_metric_schema():
    """Test that a valid metric JSON record passes validation."""
    valid_data = {
        "experiment_id": "exp-001",
        "model_name": "baseline",
        "generated_at": datetime.utcnow().isoformat(),
        "records": [
            {
                "record_id": "rec-001",
                "clip_id": "clip-001",
                "metric_type": "ssim",
                "value": 0.85,
                "unit": "unitless",
                "metadata": {"frame_idx": 10}
            }
        ],
        "total_records": 1
    }
    result = MetricValidator.validate_from_dict(valid_data)
    assert result.model_name == "baseline"
    assert result.records[0].value == 0.85


def test_invalid_metric_schema_type_mismatch():
    """Test that non-numeric value raises ValidationError."""
    invalid_data = {
        "experiment_id": "exp-002",
        "model_name": "flow",
        "generated_at": datetime.utcnow().isoformat(),
        "records": [
            {
                "record_id": "rec-002",
                "clip_id": "clip-002",
                "metric_type": "memory",
                "value": "not_a_number", # Invalid type
                "total_records": 1
            }
        ],
        "total_records": 1
    }
    with pytest.raises(ValidationError):
        MetricValidator.validate_from_dict(invalid_data)


# --- Analysis Schema Tests ---

def test_valid_analysis_schema():
    """Test that a valid analysis JSON record passes validation."""
    valid_data = {
        "report_id": "analysis-001",
        "created_at": datetime.utcnow().isoformat(),
        "comparisons": [
            {
                "result_id": "res-001",
                "analysis_type": "ks_test",
                "timestamp": datetime.utcnow().isoformat(),
                "parameters": {"alpha": 0.05},
                "results": [
                    {
                        "test_name": "KS_Test",
                        "statistic": 0.15,
                        "p_value": 0.03,
                        "conclusion": "Significant difference detected"
                    }
                ],
                "summary": "Analysis complete"
            }
        ],
        "total_comparisons": 1,
        "metadata": {}
    }
    result = AnalysisValidator.validate_from_dict(valid_data)
    assert result.report_id == "analysis-001"
    assert result.comparisons[0].results[0].p_value == 0.03


def test_invalid_analysis_schema_total_mismatch():
    """Test that mismatched total_comparisons raises ValidationError."""
    invalid_data = {
        "report_id": "analysis-002",
        "created_at": datetime.utcnow().isoformat(),
        "comparisons": [],
        "total_comparisons": 3, # Claims 3, but list is empty
        "metadata": {}
    }
    with pytest.raises(ValidationError) as exc_info:
        AnalysisValidator.validate_from_dict(invalid_data)
    assert "total_comparisons" in str(exc_info.value).lower()
