import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.data.feasibility_filter import FeasibilityFilter, GarmentFeatureClass

@pytest.fixture
def mock_config():
    return {
        "model": {
            "vlm_confidence_threshold": 0.8,
            "blip_model_id": "Salesforce/blip-large"
        },
        "motion": {
            "optical_flow_threshold": 10.0
        }
    }

@pytest.fixture
def sample_manifest(mock_config):
    # Create a temporary manifest with various samples
    samples = [
        {
            "id": "1",
            "garment_feature_class": "color",
            "vlm_confidence": 0.95,
            "optical_flow_magnitude": 15.0,
            "attributes": {"color": "red"}
        },
        {
            "id": "2",
            "garment_feature_class": "pattern",
            "vlm_confidence": 0.75, # Low confidence
            "optical_flow_magnitude": 12.0,
            "attributes": {"pattern": "striped"}
        },
        {
            "id": "3",
            "garment_feature_class": "ambiguous",
            "vlm_confidence": 0.90,
            "optical_flow_magnitude": 8.0,
            "attributes": {}
        },
        {
            "id": "4",
            "garment_feature_class": "texture",
            "vlm_confidence": 0.85,
            "optical_flow_magnitude": None, # Missing flow
            "attributes": {"texture": "smooth"}
        },
        {
            "id": "5",
            "garment_feature_class": "color",
            "vlm_confidence": 0.82,
            "optical_flow_magnitude": 20.0,
            "attributes": {"color": "blue"}
        }
    ]
    return samples

def test_filter_removes_low_confidence(sample_manifest, mock_config):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name

    try:
        # Mock load_config to return our mock config
        with patch('src.data.feasibility_filter.load_config', return_value=mock_config):
            filter_engine = FeasibilityFilter("dummy.yaml")
            result = filter_engine.run_pipeline(input_path, output_path)

            assert result['valid_count'] == 2 # Samples 1 and 5
            assert result['excluded_count'] == 3 # Samples 2, 3, 4
            
            # Verify output file content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data['samples']) == 2
            assert len(data['excluded_samples']) == 3
            
            # Check that valid samples have the required fields
            for sample in data['samples']:
                assert 'optical_flow_magnitude' in sample
                assert 'filtering_threshold' in sample
                assert sample['filtering_threshold'] == 0.8

    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)

def test_filter_removes_ambiguous_class(sample_manifest, mock_config):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name

    try:
        with patch('src.data.feasibility_filter.load_config', return_value=mock_config):
            filter_engine = FeasibilityFilter("dummy.yaml")
            result = filter_engine.run_pipeline(input_path, output_path)

            # Sample 3 is ambiguous
            assert result['excluded_count'] >= 1 
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            for excluded in data['excluded_samples']:
                if excluded['id'] == '3':
                    assert any("ambiguous" in reason.lower() for reason in excluded['exclusion_reasons'])
                    break
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)

def test_filter_removes_missing_flow(sample_manifest, mock_config):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_manifest, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name

    try:
        with patch('src.data.feasibility_filter.load_config', return_value=mock_config):
            filter_engine = FeasibilityFilter("dummy.yaml")
            result = filter_engine.run_pipeline(input_path, output_path)

            # Sample 4 has missing flow
            assert result['excluded_count'] >= 1

            with open(output_path, 'r') as f:
                data = json.load(f)
            
            for excluded in data['excluded_samples']:
                if excluded['id'] == '4':
                    assert any("Missing optical_flow_magnitude" in reason for reason in excluded['exclusion_reasons'])
                    break
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)
