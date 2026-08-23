"""
Unit tests for stratified subset selection logic.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.data.stratified_subset import (
    load_filtered_manifest,
    stratify_samples,
    validate_subset_balance,
    save_stratified_subset,
    run_pipeline
)
from src.data.feasibility_filter import GarmentFeatureClass

@pytest.fixture
def mock_filtered_samples():
    """Create mock filtered samples with various feature classes."""
    return [
        {
            "image_id": f"img_{i}",
            "garment_feature_class": GarmentFeatureClass.COLOR.value,
            "confidence": 0.95
        }
        for i in range(50)
    ] + [
        {
            "image_id": f"pat_{i}",
            "garment_feature_class": GarmentFeatureClass.PATTERN.value,
            "confidence": 0.92
        }
        for i in range(40)
    ] + [
        {
            "image_id": f"tex_{i}",
            "garment_feature_class": GarmentFeatureClass.TEXTURE.value,
            "confidence": 0.88
        }
        for i in range(30)
    ]

@pytest.fixture
def temp_manifest_file(mock_filtered_samples):
    """Create a temporary manifest file with mock samples."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_filtered_samples, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()

def test_load_filtered_manifest_valid_file(temp_manifest_file, mock_filtered_samples):
    """Test loading a valid manifest file."""
    samples = load_filtered_manifest(temp_manifest_file)
    assert len(samples) == len(mock_filtered_samples)
    assert samples[0]["image_id"] == "img_0"
    assert samples[0]["garment_feature_class"] == GarmentFeatureClass.COLOR.value

def test_load_filtered_manifest_not_found():
    """Test loading a non-existent manifest file raises error."""
    with pytest.raises(FileNotFoundError):
        load_filtered_manifest(Path("non_existent_file.json"))

def test_stratify_samples_balanced_selection(mock_filtered_samples):
    """Test that stratify_samples selects balanced samples."""
    target_per_class = 20
    stratified, counts = stratify_samples(mock_filtered_samples, target_per_class)
    
    # Should select exactly target_per_class from each class that has enough samples
    assert counts[GarmentFeatureClass.COLOR.value] == target_per_class
    assert counts[GarmentFeatureClass.PATTERN.value] == target_per_class
    assert counts[GarmentFeatureClass.TEXTURE.value] == target_per_class
    
    # Total should be target_per_class * 3
    assert len(stratified) == target_per_class * 3

def test_stratify_samples_limited_by_available(mock_filtered_samples):
    """Test stratify_samples when some classes have fewer samples than target."""
    # Set target higher than some classes have
    target_per_class = 100
    stratified, counts = stratify_samples(mock_filtered_samples, target_per_class)
    
    # Should select all available samples from each class
    assert counts[GarmentFeatureClass.COLOR.value] == 50
    assert counts[GarmentFeatureClass.PATTERN.value] == 40
    assert counts[GarmentFeatureClass.TEXTURE.value] == 30
    
    # Total should be sum of all available
    assert len(stratified) == 50 + 40 + 30

def test_stratify_samples_handles_unknown_class():
    """Test that samples without valid feature class go to 'unknown' bucket."""
    samples = [
        {"image_id": "img1", "garment_feature_class": "invalid_class"},
        {"image_id": "img2", "garment_feature_class": GarmentFeatureClass.COLOR.value},
    ]
    
    stratified, counts = stratify_samples(samples, target_size_per_class=10)
    
    assert counts.get("unknown", 0) == 1
    assert counts.get(GarmentFeatureClass.COLOR.value, 0) == 1
    assert len(stratified) == 2

def test_validate_subset_balance_perfect(mock_filtered_samples):
    """Test validation with perfectly balanced subset."""
    # Create a perfectly balanced subset
    balanced_samples = [
        {"image_id": f"img_{i}", "garment_feature_class": GarmentFeatureClass.COLOR.value}
        for i in range(30)
    ] + [
        {"image_id": f"pat_{i}", "garment_feature_class": GarmentFeatureClass.PATTERN.value}
        for i in range(30)
    ] + [
        {"image_id": f"tex_{i}", "garment_feature_class": GarmentFeatureClass.TEXTURE.value}
        for i in range(30)
    ]
    
    is_balanced, details = validate_subset_balance(balanced_samples)
    
    assert is_balanced is True
    assert details["total_samples"] == 90
    assert details["num_classes"] == 3
    assert len(details["issues"]) == 0

def test_validate_subset_balance_imbalanced():
    """Test validation detects imbalanced subsets."""
    # Create an imbalanced subset
    imbalanced_samples = [
        {"image_id": f"img_{i}", "garment_feature_class": GarmentFeatureClass.COLOR.value}
        for i in range(100)
    ] + [
        {"image_id": f"pat_{i}", "garment_feature_class": GarmentFeatureClass.PATTERN.value}
        for i in range(10)
    ]
    
    is_balanced, details = validate_subset_balance(imbalanced_samples, tolerance_percent=50.0)
    
    assert is_balanced is False
    assert len(details["issues"]) > 0

def test_validate_subset_balance_empty():
    """Test validation with empty sample list."""
    is_balanced, details = validate_subset_balance([])
    
    assert is_balanced is False
    assert "error" in details

def test_save_stratified_subset_creates_file(mock_filtered_samples):
    """Test that save_stratified_subset creates the output file."""
    stratified, counts = stratify_samples(mock_filtered_samples, target_size_per_class=10)
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        save_stratified_subset(stratified, counts, output_path)
        
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "subset_info" in data
        assert "samples" in data
        assert len(data["samples"]) == len(stratified)
    finally:
        output_path.unlink()

@patch('src.data.stratified_subset.load_filtered_manifest')
@patch('src.data.stratified_subset.stratify_samples')
@patch('src.data.stratified_subset.validate_subset_balance')
@patch('src.data.stratified_subset.save_stratified_subset')
def test_run_pipeline_integration(
    mock_save,
    mock_validate,
    mock_stratify,
    mock_load,
    mock_filtered_samples
):
    """Test the full run_pipeline function."""
    # Setup mocks
    mock_load.return_value = mock_filtered_samples
    mock_stratify.return_value = (mock_filtered_samples[:50], {"color": 50})
    mock_validate.return_value = (True, {"is_balanced": True})
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as input_f:
        input_path = Path(input_f.name)
        json.dump(mock_filtered_samples, input_f)
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_f:
        output_path = Path(output_f.name)
    
    try:
        results = run_pipeline(
            filtered_manifest_path=input_path,
            output_subset_path=output_path,
            target_size_per_class=50,
            validate=True
        )
        
        # Verify mocks were called
        mock_load.assert_called_once()
        mock_stratify.assert_called_once()
        mock_validate.assert_called_once()
        mock_save.assert_called_once()
        
        # Verify results structure
        assert "total_input_samples" in results
        assert "total_output_samples" in results
        assert "class_counts" in results
        assert "output_path" in results
    finally:
        input_path.unlink()
        output_path.unlink()