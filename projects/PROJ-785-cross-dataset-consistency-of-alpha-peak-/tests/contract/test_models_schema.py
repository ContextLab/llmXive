"""
Contract tests for the data models.

These tests verify that the model classes conform to the expected schemas
defined in the project contracts.
"""

import pytest
from pathlib import Path
import tempfile
import json

from models.eeg_dataset import EEGDataset
from models.apf_result import APFResult
from models.variance_component import VarianceComponent


class TestEEGDatasetSchema:
    """Contract tests for EEGDataset schema."""
    
    def test_schema_required_fields(self):
        """Test that all required fields are present in the schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = EEGDataset(
                dataset_id="ds003775",
                root_path=Path(tmpdir),
                subject_ids=["sub-01"],
                sampling_frequency=256.0,
                power_line_frequency=60.0
            )
            
            data = dataset.to_dict()
            
            # Required fields from the contract
            required_fields = [
                "dataset_id",
                "root_path",
                "subject_ids",
                "sampling_frequency",
                "power_line_frequency"
            ]
            
            for field in required_fields:
                assert field in data, f"Required field '{field}' missing from schema"
    
    def test_schema_types(self):
        """Test that field types match the contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = EEGDataset(
                dataset_id="ds003775",
                root_path=Path(tmpdir),
                subject_ids=["sub-01"],
                sampling_frequency=256.0,
                power_line_frequency=60.0,
                task="rest",
                checksum="abc123"
            )
            
            data = dataset.to_dict()
            
            assert isinstance(data["dataset_id"], str)
            assert isinstance(data["root_path"], str)  # Path converted to string
            assert isinstance(data["subject_ids"], list)
            assert isinstance(data["sampling_frequency"], float)
            assert isinstance(data["power_line_frequency"], float)
            assert isinstance(data["task"], str) or data["task"] is None
            assert isinstance(data["checksum"], str) or data["checksum"] is None
    
    def test_schema_optional_fields(self):
        """Test that optional fields can be None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = EEGDataset(
                dataset_id="ds003775",
                root_path=Path(tmpdir)
                # No optional fields provided
            )
            
            data = dataset.to_dict()
            
            assert data["subject_ids"] == []
            assert data["sampling_frequency"] is None
            assert data["channel_layout"] == {}
            assert data["power_line_frequency"] is None
            assert data["task"] is None
            assert data["checksum"] is None


class TestAPFResultSchema:
    """Contract tests for APFResult schema."""
    
    def test_schema_required_fields(self):
        """Test that all required fields are present in the schema."""
        result = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_hz=10.5,
            status="valid"
        )
        
        data = result.to_dict()
        
        required_fields = [
            "subject_id",
            "dataset_id",
            "pipeline_type",
            "estimation_method",
            "status",
            "processing_timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from schema"
    
    def test_schema_enum_values(self):
        """Test that enum fields have valid values."""
        # Test valid pipeline_type
        result_a = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_hz=10.5
        )
        assert result_a.to_dict()["pipeline_type"] in ["pipeline_a", "pipeline_b"]
        
        result_b = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_b",
            estimation_method="autocorr",
            apf_hz=11.0
        )
        assert result_b.to_dict()["pipeline_type"] in ["pipeline_a", "pipeline_b"]
        
        # Test valid estimation_method
        assert result_a.to_dict()["estimation_method"] in ["psd", "autocorr"]
        assert result_b.to_dict()["estimation_method"] in ["psd", "autocorr"]
        
        # Test valid status
        valid_result = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_hz=10.5,
            status="valid"
        )
        indeterminate_result = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            status="indeterminate"
        )
        out_of_band_result = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_hz=7.5,
            status="out_of_band"
        )
        
        assert valid_result.to_dict()["status"] in ["valid", "indeterminate", "out_of_band"]
        assert indeterminate_result.to_dict()["status"] in ["valid", "indeterminate", "out_of_band"]
        assert out_of_band_result.to_dict()["status"] in ["valid", "indeterminate", "out_of_band"]
    
    def test_schema_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        result = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_hz=10.5
        )
        
        data = result.to_dict()
        timestamp_str = data["processing_timestamp"]
        
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp_str)

class TestVarianceComponentSchema:
    """Contract tests for VarianceComponent schema."""
    
    def test_schema_required_fields(self):
        """Test that all required fields are present in the schema."""
        component = VarianceComponent(
            source="dataset_source",
            variance_estimate=0.45
        )
        
        data = component.to_dict()
        
        required_fields = [
            "source",
            "variance_estimate",
            "analysis_timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from schema"
    
    def test_schema_types(self):
        """Test that field types match the contract."""
        component = VarianceComponent(
            source="dataset_source",
            variance_estimate=0.45,
            percentage_of_total=45.0,
            confidence_interval_lower=0.40,
            confidence_interval_upper=0.50,
            model_id="model_001"
        )
        
        data = component.to_dict()
        
        assert isinstance(data["source"], str)
        assert isinstance(data["variance_estimate"], float)
        assert isinstance(data["percentage_of_total"], float) or data["percentage_of_total"] is None
        assert isinstance(data["confidence_interval_lower"], float) or data["confidence_interval_lower"] is None
        assert isinstance(data["confidence_interval_upper"], float) or data["confidence_interval_upper"] is None
        assert isinstance(data["model_id"], str) or data["model_id"] is None
    
    def test_schema_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        component = VarianceComponent(
            source="dataset_source",
            variance_estimate=0.45
        )
        
        data = component.to_dict()
        timestamp_str = data["analysis_timestamp"]
        
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp_str)

def test_json_serialization_compatibility():
    """Test that all models can be serialized to JSON and back."""
    import json
    from datetime import datetime
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create instances
        dataset = EEGDataset(
            dataset_id="ds003775",
            root_path=Path(tmpdir),
            subject_ids=["sub-01"],
            sampling_frequency=256.0,
            power_line_frequency=60.0
        )
        
        apf_result = APFResult(
            subject_id="sub-01",
            dataset_id="ds003775",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_hz=10.5
        )
        
        variance_component = VarianceComponent(
            source="dataset_source",
            variance_estimate=0.45,
            percentage_of_total=45.0
        )
        
        # Convert to dict and then to JSON
        dataset_json = json.dumps(dataset.to_dict())
        apf_json = json.dumps(apf_result.to_dict())
        variance_json = json.dumps(variance_component.to_dict())
        
        # Parse back
        dataset_parsed = json.loads(dataset_json)
        apf_parsed = json.loads(apf_json)
        variance_parsed = json.loads(variance_json)
        
        # Verify roundtrip
        assert dataset_parsed["dataset_id"] == dataset.dataset_id
        assert apf_parsed["apf_hz"] == apf_result.apf_hz
        assert variance_parsed["variance_estimate"] == variance_component.variance_estimate