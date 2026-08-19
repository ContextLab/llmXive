import os
import pytest
import pandas as pd
import tempfile
from code.data.validation import (
    validate_final_results_schema,
    validate_unique_subjects,
    validate_final_results_file,
    run_validation_pipeline
)

def test_validate_final_results_schema_valid():
    """Test schema validation with a valid DataFrame."""
    df = pd.DataFrame({
        'Subject_ID': ['S001', 'S002'],
        'Mean_FD': [0.1, 0.2],
        'Age': [25, 30],
        'Sex': ['M', 'F'],
        'Flexibility_Score': [0.8, 0.9],
        'Variability_Metric': [0.5, 0.6],
        'Entropy': [0.7, 0.8]
    })
    
    is_valid, missing_cols = validate_final_results_schema(df)
    assert is_valid is True
    assert len(missing_cols) == 0

def test_validate_final_results_schema_missing_columns():
    """Test schema validation with missing columns."""
    df = pd.DataFrame({
        'Subject_ID': ['S001'],
        'Mean_FD': [0.1]
    })
    
    is_valid, missing_cols = validate_final_results_schema(df)
    assert is_valid is False
    assert 'Age' in missing_cols
    assert 'Sex' in missing_cols
    assert 'Flexibility_Score' in missing_cols
    assert 'Variability_Metric' in missing_cols
    assert 'Entropy' in missing_cols

def test_validate_final_results_schema_empty():
    """Test schema validation with an empty DataFrame."""
    df = pd.DataFrame()
    
    is_valid, missing_cols = validate_final_results_schema(df)
    assert is_valid is False
    assert len(missing_cols) > 0

def test_validate_unique_subjects_valid():
    """Test uniqueness validation with unique subjects."""
    df = pd.DataFrame({
        'Subject_ID': ['S001', 'S002', 'S003'],
        'Mean_FD': [0.1, 0.2, 0.3]
    })
    
    is_valid, dup_count = validate_unique_subjects(df)
    assert is_valid is True
    assert dup_count == 0

def test_validate_unique_subjects_duplicates():
    """Test uniqueness validation with duplicate subjects."""
    df = pd.DataFrame({
        'Subject_ID': ['S001', 'S001', 'S002'],
        'Mean_FD': [0.1, 0.2, 0.3]
    })
    
    is_valid, dup_count = validate_unique_subjects(df)
    assert is_valid is False
    assert dup_count == 1

def test_validate_unique_subjects_no_column():
    """Test uniqueness validation when Subject_ID column is missing."""
    df = pd.DataFrame({
        'Mean_FD': [0.1, 0.2]
    })
    
    is_valid, dup_count = validate_unique_subjects(df)
    assert is_valid is False
    assert dup_count == -1

def test_validate_final_results_file_valid():
    """Test file validation with a valid CSV."""
    df = pd.DataFrame({
        'Subject_ID': ['S001', 'S002'],
        'Mean_FD': [0.1, 0.2],
        'Age': [25, 30],
        'Sex': ['M', 'F'],
        'Flexibility_Score': [0.8, 0.9],
        'Variability_Metric': [0.5, 0.6],
        'Entropy': [0.7, 0.8]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        result = validate_final_results_file(temp_path)
        assert result['valid'] is True
        assert result['subject_count'] == 2
        assert result['row_count'] == 2
        assert len(result['errors']) == 0
    finally:
        os.unlink(temp_path)

def test_validate_final_results_file_missing():
    """Test file validation with a missing file."""
    result = validate_final_results_file('/nonexistent/path/file.csv')
    assert result['valid'] is False
    assert len(result['errors']) > 0

def test_validate_final_results_file_duplicates():
    """Test file validation with duplicate subjects in CSV."""
    df = pd.DataFrame({
        'Subject_ID': ['S001', 'S001', 'S002'],
        'Mean_FD': [0.1, 0.2, 0.3],
        'Age': [25, 30, 35],
        'Sex': ['M', 'F', 'M'],
        'Flexibility_Score': [0.8, 0.9, 0.7],
        'Variability_Metric': [0.5, 0.6, 0.4],
        'Entropy': [0.7, 0.8, 0.6]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        result = validate_final_results_file(temp_path)
        assert result['valid'] is False
        assert any("Duplicate" in err for err in result['errors'])
    finally:
        os.unlink(temp_path)
