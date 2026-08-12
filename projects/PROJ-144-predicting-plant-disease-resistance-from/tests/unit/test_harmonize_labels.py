import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from pathlib import Path

# Import the function to test
import sys
sys.path.insert(0, 'code')
from data.harmonize_labels import harmonize_labels

@pytest.fixture
def sample_labels_csv():
    """Create a temporary CSV file with sample label data."""
    data = {
        'germplasm_id': ['G1', 'G2', 'G3', 'G4', 'G5'],
        'assay_score': [0.1, 0.3, 0.5, 0.7, 0.9] # Median is 0.5
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def cleanup_temp_files():
    yield
    # Cleanup logic if needed, though NamedTemporaryFile handles it on close usually
    pass

def test_harmonize_labels_binary_creation(sample_labels_csv):
    """Test that binary_label is created correctly based on median."""
    result_df = harmonize_labels(sample_labels_csv)
    
    assert 'binary_label' in result_df.columns
    assert 'harmonized_score' in result_df.columns
    assert 'germplasm_id' in result_df.columns
    
    # Check values: median is 0.5. <0.5 -> 0, >=0.5 -> 1
    expected_labels = [0, 0, 1, 1, 1]
    assert list(result_df['binary_label']) == expected_labels

def test_harmonize_labels_zscore(sample_labels_csv):
    """Test that harmonized_score is z-scored."""
    result_df = harmonize_labels(sample_labels_csv)
    
    # Z-score should have mean approx 0 and std approx 1
    mean_score = result_df['harmonized_score'].mean()
    std_score = result_df['harmonized_score'].std()
    
    # Allow for floating point tolerance
    assert np.isclose(mean_score, 0.0, atol=1e-6)
    assert np.isclose(std_score, 1.0, atol=1e-6)

def test_harmonize_labels_missing_columns(sample_labels_csv):
    """Test that error is raised if required columns are missing."""
    # Create a bad CSV
    data = {'germplasm_id': ['G1'], 'other_col': [1.0]}
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        bad_path = f.name
    
    try:
        with pytest.raises(ValueError) as exc_info:
            harmonize_labels(bad_path)
        assert "Missing required columns" in str(exc_info.value)
    finally:
        os.unlink(bad_path)

def test_harmonize_labels_all_same_label(sample_labels_csv):
    """Test that error is raised if all labels are the same (after harmonization)."""
    # Create data where all scores are identical
    data = {
        'germplasm_id': ['G1', 'G2', 'G3'],
        'assay_score': [0.5, 0.5, 0.5]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        bad_path = f.name
    
    try:
        with pytest.raises(ValueError) as exc_info:
            harmonize_labels(bad_path)
        assert "All samples have the same label" in str(exc_info.value)
    finally:
        os.unlink(bad_path)

def test_harmonize_labels_report_generation(sample_labels_csv):
    """Test that a validation report JSON is generated."""
    # Ensure RESULTS_DIR exists (mocked or real)
    from code.utils.constants import RESULTS_DIR
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    harmonize_labels(sample_labels_csv)
    
    report_path = os.path.join(RESULTS_DIR, "label_harmonization_report.json")
    assert os.path.exists(report_path)
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert "status" in report
    assert report["status"] == "harmonized"
    assert "class_distribution" in report
    assert "median_threshold" in report