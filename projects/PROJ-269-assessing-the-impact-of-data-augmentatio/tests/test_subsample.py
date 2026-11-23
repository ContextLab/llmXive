import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys
import json

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from subsample import (
    detect_target_column,
    validate_class_counts,
    create_stratified_subsample,
    log_skipped_configuration,
    process_dataset,
    MIN_CLASS_COUNT
)

@pytest.fixture
def sample_data():
    """Create a simple balanced dataset."""
    data = {
        'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'feature2': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'target': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def unbalanced_data():
    """Create an unbalanced dataset."""
    data = {
        'feature1': list(range(100)),
        'target': [0] * 90 + [1] * 10
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(tmp_path):
    """Create a temporary CSV file."""
    df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5, 6],
        'class': ['A', 'A', 'B', 'B', 'C', 'C']
    })
    path = tmp_path / "test_data.csv"
    df.to_csv(path, index=False)
    return path

def test_detect_target_column_priority(sample_data):
    """Test target column detection priority."""
    # 'target' exists, should be chosen
    assert detect_target_column(sample_data) == 'target'
    
    # Create a dataframe with 'class' but no 'target'
    df_class = sample_data.rename(columns={'target': 'class'})
    assert detect_target_column(df_class) == 'class'
    
    # Create a dataframe with 'label' but no 'target' or 'class'
    df_label = sample_data.rename(columns={'target': 'label'})
    assert detect_target_column(df_label) == 'label'
    
    # Create a dataframe with none of the priority names
    df_none = sample_data.rename(columns={'target': 'outcome'})
    # Should default to last column
    assert detect_target_column(df_none) == 'feature2'

def test_validate_class_counts_valid(sample_data):
    """Test validation for a valid configuration."""
    # N=4, 2 classes -> 2 per class. Min required is 5?
    # Wait, MIN_CLASS_COUNT is 5. 
    # N=4 is too small for 2 classes with min 5 per class (needs 10).
    # Let's test with a larger N that satisfies the condition.
    # Actually, the condition is: n >= num_classes * MIN_CLASS_COUNT
    # 10 >= 2 * 5 -> True.
    is_valid, counts = validate_class_counts(sample_data, 'target', 10)
    assert is_valid is True
    assert counts[0] == 5
    assert counts[1] == 5

def test_validate_class_counts_invalid_small_n(sample_data):
    """Test validation for a size too small."""
    # N=4, 2 classes. Need 10.
    is_valid, counts = validate_class_counts(sample_data, 'target', 4)
    assert is_valid is False

def test_validate_class_counts_invalid_imbalanced(unbalanced_data):
    """Test validation where a class is too small."""
    # Class 1 has only 10 items.
    # If we try N=100 (impossible anyway), but let's try N=20.
    # 2 classes. Need 10 per class.
    # Class 1 has 10. Class 0 has 90.
    # N=20 -> 10 per class.
    # This should be valid because both have >= 10.
    is_valid, counts = validate_class_counts(unbalanced_data, 'target', 20)
    assert is_valid is True
    
    # Try N=22 -> 11 per class. Class 1 has only 10.
    is_valid, counts = validate_class_counts(unbalanced_data, 'target', 22)
    assert is_valid is False

def test_create_stratified_subsample(sample_data):
    """Test stratified subsampling."""
    # N=10, 2 classes -> 5 each
    subsample = create_stratified_subsample(sample_data, 'target', 10, seed=42)
    assert len(subsample) == 10
    assert subsample['target'].value_counts()[0] == 5
    assert subsample['target'].value_counts()[1] == 5

def test_log_skipped_configuration(tmp_path):
    """Test logging of skipped configurations."""
    # Temporarily override the log path for testing
    import subsample
    original_path = subsample.SKIPPED_LOG_PATH
    test_log_path = tmp_path / "skipped.log"
    subsample.SKIPPED_LOG_PATH = test_log_path
    
    try:
        log_skipped_configuration("test_dataset", 5, "Too small")
        
        assert test_log_path.exists()
        with open(test_log_path, 'r') as f:
            content = f.read()
            assert "test_dataset" in content
            assert "Too small" in content
    finally:
        subsample.SKIPPED_LOG_PATH = original_path

def test_process_dataset_integration(tmp_path):
    """Integration test for processing a dataset."""
    # Create a temporary dataset
    df = pd.DataFrame({
        'feature1': list(range(30)),
        'target': [0]*15 + [1]*15
    })
    csv_path = tmp_path / "integration_test.csv"
    df.to_csv(csv_path, index=False)
    
    # Create a temporary output directory for derived data
    derived_dir = tmp_path / "derived"
    derived_dir.mkdir()
    
    # Patch the SKIPPED_LOG_PATH and output dir
    import subsample
    original_skipped = subsample.SKIPPED_LOG_PATH
    original_derived = Path("data/derived") # This is the global constant used in process_dataset for saving
    
    # We need to be careful not to pollute the real project data during tests.
    # The function uses Path("data/derived") directly.
    # For a true integration test without mocking, we would run in the project dir.
    # But let's just verify the logic works if the paths exist.
    
    # Instead, let's just test the logic with the temp file and a temp derived dir
    # by patching the function's internal path resolution if necessary, 
    # or just running it in a controlled environment.
    # For now, let's assume the test runs in the project root or we patch the path.
    
    # Let's just verify the function returns results if we force the paths.
    # Actually, process_dataset saves to data/derived.
    # We will create the directory structure temporarily.
    real_derived = Path("data/derived")
    real_derived.mkdir(exist_ok=True)
    
    try:
        results = process_dataset(csv_path, "integration_test", sizes=[10])
        
        assert len(results) == 1
        assert results[0]['dataset'] == 'integration_test'
        assert results[0]['size'] == 10
        assert results[0]['row_count'] == 10
        
        # Check if file was created
        output_file = Path(results[0]['output_path'])
        assert output_file.exists()
        
        # Verify content
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) == 10
    finally:
        # Cleanup
        import shutil
        if real_derived.exists():
            # Remove only the test file we created
            for f in real_derived.glob("integration_test*.csv"):
                f.unlink()
        # Remove log if created
        if Path("data/derived/skipped_configurations.log").exists():
             # In a real test suite, we might want to be more careful
             pass
