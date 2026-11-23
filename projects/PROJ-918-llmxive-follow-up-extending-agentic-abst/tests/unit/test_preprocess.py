import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from data.preprocess import (
    calculate_missing_statistics,
    perform_mean_imputation,
    validate_dataset,
    generate_validation_report,
    load_preprocessing_config
)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with some missing values."""
    data = {
        "search_count": [1, 2, np.nan, 4, 5],
        "error_frequency": [0.1, 0.2, 0.3, np.nan, 0.5],
        "token_usage": [100, 200, 300, 400, np.nan],
        "turn_number": [1, 2, 3, 4, 5],
        "embedding_distance": [0.1, 0.2, 0.3, 0.4, 0.5],
        "abstention_label": [0, 1, 0, 1, 0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def critical_columns():
    return ["search_count", "error_frequency", "token_usage", "turn_number", "embedding_distance", "abstention_label"]

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_missing_statistics(sample_dataframe, critical_columns):
    """Test missing value statistics calculation."""
    stats = calculate_missing_statistics(sample_dataframe, critical_columns)
    
    assert "search_count" in stats
    assert stats["search_count"]["missing_count"] == 1
    assert stats["search_count"]["missing_ratio"] == 0.2
    
    assert "_summary" in stats
    assert stats["_summary"]["total_critical_columns"] == len(critical_columns)

def test_perform_mean_imputation(sample_dataframe, critical_columns):
    """Test mean imputation logic."""
    # Filter to numeric critical columns
    numeric_critical = [col for col in critical_columns if col in sample_dataframe.select_dtypes(include=[np.number]).columns]
    
    df_imputed, imputation_info = perform_mean_imputation(sample_dataframe, numeric_critical)
    
    # Check that no NaN values remain in imputed columns
    for col in numeric_critical:
        assert not df_imputed[col].isna().any(), f"Column {col} still has missing values"
    
    # Check that imputation info is populated
    assert len(imputation_info) > 0

def test_validate_dataset_valid(sample_dataframe, critical_columns):
    """Test validation with a valid dataset."""
    stats = calculate_missing_statistics(sample_dataframe, critical_columns)
    is_valid = validate_dataset(sample_dataframe, stats, 0.05)
    
    # With 1/5 missing in one column (20%), this should fail the 5% threshold
    # But the overall ratio might be lower. Let's test the logic.
    # Overall ratio = (0.2 + 0.2 + 0.2 + 0 + 0 + 0) / 6 = 0.1
    # 0.1 > 0.05, so it should be False
    assert is_valid == False

def test_validate_dataset_highly_complete(temp_dir):
    """Test validation with a highly complete dataset."""
    data = {
        "search_count": [1.0, 2.0, 3.0, 4.0, 5.0],
        "error_frequency": [0.1, 0.2, 0.3, 0.4, 0.5],
        "token_usage": [100.0, 200.0, 300.0, 400.0, 500.0],
        "turn_number": [1, 2, 3, 4, 5],
        "embedding_distance": [0.1, 0.2, 0.3, 0.4, 0.5],
        "abstention_label": [0, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    
    critical_columns = ["search_count", "error_frequency", "token_usage", "turn_number", "embedding_distance", "abstention_label"]
    stats = calculate_missing_statistics(df, critical_columns)
    
    is_valid = validate_dataset(df, stats, 0.05)
    assert is_valid == True

def test_generate_validation_report(temp_dir, sample_dataframe, critical_columns):
    """Test validation report generation."""
    stats = calculate_missing_statistics(sample_dataframe, critical_columns)
    is_valid = False  # Simulate failed validation
    
    report_file = temp_dir / "validation_report.json"
    report = generate_validation_report(
        sample_dataframe, 
        stats, 
        0.05, 
        is_valid,
        output_path=report_file
    )
    
    assert report_file.exists()
    assert report["validation_status"] == "FAILED"
    assert report["threshold"] == 0.05
    
    # Verify JSON content
    with open(report_file, 'r') as f:
        loaded_report = json.load(f)
    
    assert loaded_report["validation_status"] == "FAILED"

def test_halt_execution_logic(temp_dir, sample_dataframe, critical_columns):
    """Test that the halt execution logic generates a report when threshold is exceeded."""
    # Create a scenario where missing ratio > 5%
    stats = calculate_missing_statistics(sample_dataframe, critical_columns)
    
    # Simulate the main logic flow
    is_valid = validate_dataset(sample_dataframe, stats, 0.05)
    
    report_file = temp_dir / "validation_report.json"
    
    if not is_valid:
        report = generate_validation_report(
            sample_dataframe,
            stats,
            0.05,
            is_valid,
            output_path=report_file
        )
        
        assert report_file.exists()
        assert report["validation_status"] == "FAILED"
        assert "summary" in report
        assert "column_statistics" in report

def test_config_loading():
    """Test that configuration loading works."""
    config = load_preprocessing_config()
    
    assert "missing_threshold" in config
    assert "imputation_strategy" in config
    assert "critical_columns" in config
    
    assert config["missing_threshold"] == 0.05
    assert config["imputation_strategy"] == "mean"
    assert len(config["critical_columns"]) > 0