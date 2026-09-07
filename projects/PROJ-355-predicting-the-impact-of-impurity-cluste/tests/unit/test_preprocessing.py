import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.data.preprocessing import filter_zero_impurity_configs, generate_preprocessing_report

def test_filter_zero_impurity_configs_with_count():
    """Test filtering when 'impurity_count' column exists."""
    data = {
        'config_id': [1, 2, 3, 4],
        'impurity_count': [0, 1, 2, 0],
        'value': [10, 20, 30, 40]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_zero_impurity_configs(df)
    
    assert len(filtered_df) == 2
    assert excluded_count == 2
    assert all(filtered_df['impurity_count'] > 0)
    assert list(filtered_df['config_id']) == [2, 3]

def test_filter_zero_impurity_configs_with_species():
    """Test filtering when 'impurity_species' column exists."""
    data = {
        'config_id': [1, 2, 3],
        'impurity_species': ['', 'Cr', None],
        'value': [10, 20, 30]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_zero_impurity_configs(df)
    
    assert len(filtered_df) == 1
    assert excluded_count == 2
    assert list(filtered_df['config_id']) == [2]

def test_filter_empty_dataframe():
    """Test that an empty dataframe raises ValueError."""
    df = pd.DataFrame(columns=['config_id', 'impurity_count'])
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        filter_zero_impurity_configs(df)

def test_filter_missing_columns():
    """Test that missing required columns raises ValueError."""
    df = pd.DataFrame({'config_id': [1]})
    with pytest.raises(ValueError, match="missing 'impurity_count' or 'impurity_species'"):
        filter_zero_impurity_configs(df)

def test_generate_preprocessing_report(tmp_path):
    """Test report generation."""
    report_path = tmp_path / "preprocessing_report.json"
    generate_preprocessing_report(5, report_path)
    
    assert report_path.exists()
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['excluded_count'] == 5
    assert report['status'] == 'completed'
    assert 'reason' in report
