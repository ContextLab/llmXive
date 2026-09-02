"""
Contract tests for data model schemas.
Ensures models conform to expected contract definitions.
"""
import pytest
from typing import Dict, Any
import json

from models.eeg_dataset import EEGDataset
from models.apf_result import APFResult
from models.variance_component import VarianceComponent, VarianceAnalysisResult


# Expected schema definitions (simulated from contracts/)
EXPECTED_EEG_DATASET_KEYS = {
    "dataset_id", "subject_ids", "raw_path", "derivative_path",
    "sampling_frequency", "channel_count", "task", "metadata",
    "created_at", "sha256_checksum"
}

EXPECTED_APF_RESULT_KEYS = {
    "dataset_id", "subject_id", "session_id", "pipeline_type",
    "estimation_method", "apf_value", "apf_status", "peak_power",
    "lag_index", "confidence_interval", "created_at"
}

EXPECTED_VARIANCE_COMPONENT_KEYS = {
    "component_name", "variance_estimate", "proportion",
    "confidence_interval", "p_value", "model_formula",
    "dataset_id", "created_at"
}


def _validate_keys(data: Dict[str, Any], expected_keys: set, name: str):
    """Helper to validate that all expected keys are present."""
    missing = expected_keys - set(data.keys())
    extra = set(data.keys()) - expected_keys
    
    assert not missing, f"{name}: Missing keys: {missing}"
    # Extra keys are allowed for forward compatibility, but we log them
    if extra:
        print(f"Warning: {name} has extra keys: {extra}")


class TestEEGDatasetSchema:
    def test_schema_conformity(self):
        """Test that EEGDataset.to_dict() matches expected schema."""
        dataset = EEGDataset(
            dataset_id="ds003775",
            subject_ids=["sub-01"],
            sampling_frequency=256.0,
            channel_count=64,
        )
        
        data = dataset.to_dict()
        _validate_keys(data, EXPECTED_EEG_DATASET_KEYS, "EEGDataset")

    def test_required_fields_not_none(self):
        """Test that required fields are not None."""
        dataset = EEGDataset(dataset_id="ds003865", subject_ids=[])
        
        assert dataset.dataset_id is not None
        assert dataset.subject_ids is not None


class TestAPFResultSchema:
    def test_schema_conformity(self):
        """Test that APFResult.to_dict() matches expected schema."""
        result = APFResult(
            dataset_id="ds003775",
            subject_id="sub-01",
            pipeline_type="Pipeline A",
            estimation_method="psd",
        )
        
        data = result.to_dict()
        _validate_keys(data, EXPECTED_APF_RESULT_KEYS, "APFResult")

    def test_valid_enum_values(self):
        """Test that enum fields accept valid values."""
        valid_pipelines = ["Pipeline A", "Pipeline B"]
        valid_methods = ["psd", "autocorr"]
        valid_statuses = ["valid", "indeterminate", "out_of_band"]
        
        for pipe in valid_pipelines:
            for method in valid_methods:
                for status in valid_statuses:
                    result = APFResult(
                        dataset_id="ds003775",
                        subject_id="sub-01",
                        pipeline_type=pipe,
                        estimation_method=method,
                        apf_status=status,
                    )
                    assert result.pipeline_type == pipe
                    assert result.estimation_method == method
                    assert result.apf_status == status


class TestVarianceComponentSchema:
    def test_schema_conformity(self):
        """Test that VarianceComponent.to_dict() matches expected schema."""
        component = VarianceComponent(
            component_name="dataset_source",
            variance_estimate=0.5,
        )
        
        data = component.to_dict()
        _validate_keys(data, EXPECTED_VARIANCE_COMPONENT_KEYS, "VarianceComponent")

    def test_variance_analysis_result_schema(self):
        """Test VarianceAnalysisResult schema."""
        analysis = VarianceAnalysisResult(
            components=[
                VarianceComponent(component_name="test", variance_estimate=1.0)
            ],
            total_variance=2.0,
        )
        
        data = analysis.to_dict()
        
        assert "components" in data
        assert "total_variance" in data
        assert "residual_variance" in data
        assert "model_fit_stats" in data
        assert "created_at" in data