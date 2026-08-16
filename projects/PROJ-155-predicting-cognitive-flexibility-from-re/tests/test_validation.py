"""
Tests for the validation module.

These tests verify that the validation logic correctly identifies
schema issues and duplicate subjects in the final_results.csv file.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from code.data.validation import (
    validate_final_results_schema,
    validate_unique_subjects,
    validate_final_results_file,
    run_validation_pipeline
)
from code.data.paths import get_processed_path, ensure_dir

@pytest.fixture
def valid_dataframe():
    """Create a valid DataFrame for testing."""
    data = {
        'Subject_ID': ['1001', '1002', '1003', '1004', '1005'],
        'Variability_Metric': [0.12, 0.15, 0.18, 0.14, 0.16],
        'Flexibility_Score': [45.2, 52.1, 48.7, 50.3, 49.8],
        'Covariates': ['{"age": 25, "sex": "M"}', '{"age": 30, "sex": "F"}', 
                     '{"age": 28, "sex": "M"}', '{"age": 22, "sex": "F"}',
                     '{"age": 35, "sex": "M"}'],
        'Predicted_Score': [46.1, 51.8, 49.2, 50.1, 49.5],
        'Residual': [-0.9, 0.3, -0.5, 0.2, 0.3],
        'Beta_Variability': [1.2],
        'SE_Variability': [0.15],
        'P_Value': [0.001]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_schema_dataframe():
    """Create a DataFrame with missing columns."""
    data = {
        'Subject_ID': ['1001', '1002'],
        'Variability_Metric': [0.12, 0.15],
        # Missing Flexibility_Score and other required columns
    }
    return pd.DataFrame(data)

@pytest.fixture
def duplicate_subject_dataframe():
    """Create a DataFrame with duplicate subjects."""
    data = {
        'Subject_ID': ['1001', '1001', '1002', '1003'],
        'Variability_Metric': [0.12, 0.13, 0.15, 0.18],
        'Flexibility_Score': [45.2, 46.1, 52.1, 48.7],
        'Covariates': ['{"age": 25, "sex": "M"}'] * 4,
        'Predicted_Score': [46.1, 46.5, 51.8, 49.2],
        'Residual': [-0.9, -0.4, 0.3, -0.5],
        'Beta_Variability': [1.2],
        'SE_Variability': [0.15],
        'P_Value': [0.001]
    }
    return pd.DataFrame(data)

def test_validate_final_results_schema_valid(valid_dataframe):
    """Test schema validation with valid data."""
    is_valid, errors = validate_final_results_schema(valid_dataframe)
    
    assert is_valid is True
    assert len(errors) == 0

def test_validate_final_results_schema_missing_columns(invalid_schema_dataframe):
    """Test schema validation with missing columns."""
    is_valid, errors = validate_final_results_schema(invalid_schema_dataframe)
    
    assert is_valid is False
    assert len(errors) > 0
    assert any("Missing required columns" in err for err in errors)

def test_validate_unique_subjects_valid(valid_dataframe):
    """Test unique subject validation with valid data."""
    is_valid, errors = validate_unique_subjects(valid_dataframe)
    
    assert is_valid is True
    assert len(errors) == 0

def test_validate_unique_subjects_duplicates(duplicate_subject_dataframe):
    """Test unique subject validation with duplicates."""
    is_valid, errors = validate_unique_subjects(duplicate_subject_dataframe)
    
    assert is_valid is False
    assert len(errors) > 0
    assert any("duplicate" in err.lower() for err in errors)
    assert "1001" in str(errors)

def test_validate_final_results_file_missing_file():
    """Test validation when file does not exist."""
    is_valid, errors, row_count = validate_final_results_file("/nonexistent/path.csv")
    
    assert is_valid is False
    assert len(errors) == 1
    assert "not found" in errors[0].lower()
    assert row_count == 0

def test_run_validation_pipeline_valid_file(valid_dataframe, tmp_path):
    """Test the full validation pipeline with a valid file."""
    # Create a temporary valid CSV file
    csv_path = os.path.join(tmp_path, "final_results.csv")
    valid_dataframe.to_csv(csv_path, index=False)
    
    result = run_validation_pipeline(csv_path)
    
    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert result['row_count'] == 5
    assert result['unique_subjects'] == 5

def test_run_validation_pipeline_invalid_schema(tmp_path, invalid_schema_dataframe):
    """Test the full validation pipeline with invalid schema."""
    csv_path = os.path.join(tmp_path, "final_results.csv")
    invalid_schema_dataframe.to_csv(csv_path, index=False)
    
    result = run_validation_pipeline(csv_path)
    
    assert result['valid'] is False
    assert len(result['errors']) > 0

def test_run_validation_pipeline_duplicates(tmp_path, duplicate_subject_dataframe):
    """Test the full validation pipeline with duplicate subjects."""
    csv_path = os.path.join(tmp_path, "final_results.csv")
    duplicate_subject_dataframe.to_csv(csv_path, index=False)
    
    result = run_validation_pipeline(csv_path)
    
    assert result['valid'] is False
    assert len(result['errors']) > 0
    assert any("duplicate" in err.lower() for err in result['errors'])
