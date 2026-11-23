import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from pathlib import Path

# Import the function to test
try:
    from code.data.harmonize_labels import harmonize_labels
except ImportError:
    from data.harmonize_labels import harmonize_labels

@pytest.fixture
def sample_labels_csv(tmp_path):
    """Create a temporary CSV file with sample labels for testing."""
    data = {
        'germplasm_id': ['G1', 'G2', 'G3', 'G4', 'G5'],
        'assay_score': [0.2, 0.8, 0.5, 0.9, 0.1],
        'measurement_method': ['bioassay', 'bioassay', 'genomic', 'bioassay', 'bioassay']
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test_labels.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def constant_labels_csv(tmp_path):
    """Create a temporary CSV file where all labels are the same (should fail)."""
    data = {
        'germplasm_id': ['G1', 'G2', 'G3'],
        'assay_score': [0.5, 0.5, 0.5],
        'measurement_method': ['bioassay', 'bioassay', 'bioassay']
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "constant_labels.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

def test_harmonize_labels_creates_columns(sample_labels_csv):
    """Test that harmonize_labels creates the required columns."""
    result = harmonize_labels(sample_labels_csv)
    
    assert 'binary_label' in result.columns
    assert 'harmonized_score' in result.columns
    assert 'germplasm_id' in result.columns
    assert 'assay_score' in result.columns

def test_harmonize_labels_binary_mapping(sample_labels_csv):
    """Test that binary labels are correctly mapped (0 or 1)."""
    result = harmonize_labels(sample_labels_csv)
    
    unique_labels = result['binary_label'].unique()
    assert set(unique_labels).issubset({0, 1}), "Binary labels must be 0 or 1"
    
    # Check that the median split works as expected
    # Data: [0.2, 0.8, 0.5, 0.9, 0.1] -> Median is 0.5
    # Expected: 0.2->0, 0.8->1, 0.5->1 (>=), 0.9->1, 0.1->0
    expected_labels = [0, 1, 1, 1, 0]
    assert list(result['binary_label']) == expected_labels, f"Expected {expected_labels}, got {list(result['binary_label'])}"

def test_harmonize_labels_z_score(sample_labels_csv):
    """Test that harmonized_score is z-scored."""
    result = harmonize_labels(sample_labels_csv)
    
    # Z-scored data should have mean ~0 and std ~1
    mean_score = result['harmonized_score'].mean()
    std_score = result['harmonized_score'].std()
    
    assert np.isclose(mean_score, 0.0, atol=1e-5), f"Mean of z-scored data should be ~0, got {mean_score}"
    assert np.isclose(std_score, 1.0, atol=1e-5), f"Std of z-scored data should be ~1, got {std_score}"

def test_harmonize_labels_constant_variance_raises_error(constant_labels_csv):
    """Test that constant variance in assay_score raises a warning but doesn't crash, setting score to 0."""
    # Note: The implementation handles zero variance by setting harmonized_score to 0.0
    # It only raises ValueError if ALL labels end up the same after binarization.
    # With constant 0.5, median is 0.5, so all become 1 -> should raise ValueError.
    with pytest.raises(ValueError, match="All samples have the same label"):
        harmonize_labels(constant_labels_csv)

def test_harmonize_labels_missing_columns_raises_error(tmp_path):
    """Test that missing required columns raises an error."""
    csv_path = tmp_path / "bad_labels.csv"
    pd.DataFrame({'germplasm_id': ['G1']}).to_csv(csv_path, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        harmonize_labels(str(csv_path))

def test_harmonize_labels_report_created(sample_labels_csv, tmp_path):
    """Test that the harmonization report is created."""
    # Temporarily override RESULTS_DIR for the test
    import code.data.harmonize_labels as module
    original_results_dir = module.RESULTS_DIR
    module.RESULTS_DIR = str(tmp_path / "results")
    
    try:
        harmonize_labels(sample_labels_csv)
        
        report_path = os.path.join(module.RESULTS_DIR, "label_harmonization_report.json")
        assert os.path.exists(report_path), "Harmonization report should be created"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert 'total_samples' in report
        assert 'median_threshold' in report
        assert 'class_distribution' in report
        assert report['status'] == 'harmonized'
    finally:
        module.RESULTS_DIR = original_results_dir