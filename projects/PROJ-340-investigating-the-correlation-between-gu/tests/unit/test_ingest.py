"""
Unit tests for code/ingest.py
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.ingest import (
    load_schema,
    validate_variables,
    save_variable_metrics,
    load_data,
    detect_outliers_iqr,
    filter_outliers
)


@pytest.fixture
def temp_schema_dir():
    """Create a temporary directory with a mock schema file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "dataset.schema.yaml"
        schema_content = """
        predictors:
          required:
            - Bacteroides
            - Firmicutes
        outcomes:
          required:
            - SWS duration
            - REM latency
        """
        schema_path.write_text(schema_content)
        yield schema_path


@pytest.fixture
def mock_dataframe():
    """Create a mock DataFrame with all required columns."""
    data = {
        'Bacteroides': [100, 200, 300],
        'Firmicutes': [50, 60, 70],
        'SWS duration': [120, 130, 140],
        'REM latency': [90, 95, 100],
        'extra_col': [1, 2, 3]
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_dataframe_missing():
    """Create a mock DataFrame missing a required column."""
    data = {
        'Bacteroides': [100, 200, 300],
        'Firmicutes': [50, 60, 70],
        # 'SWS duration' is missing
        'REM latency': [90, 95, 100],
    }
    return pd.DataFrame(data)


def test_validate_variables_success(mock_dataframe, temp_schema_dir):
    """Test validation when all required variables are present."""
    schema = load_schema(temp_schema_dir)
    is_valid, metrics = validate_variables(mock_dataframe, schema)
    
    assert is_valid is True
    assert metrics['missing_count'] == 0
    assert metrics['percentage_loaded'] == 100.0
    assert metrics['status'] == 'valid'


def test_validate_variables_failure(mock_dataframe_missing, temp_schema_dir):
    """Test validation when a required variable is missing."""
    schema = load_schema(temp_schema_dir)
    is_valid, metrics = validate_variables(mock_dataframe_missing, schema)
    
    assert is_valid is False
    assert metrics['missing_count'] == 1
    assert 'SWS duration' in metrics['missing_variables']
    assert metrics['percentage_loaded'] < 100.0
    assert metrics['status'] == 'invalid'


def test_save_variable_metrics(temp_schema_dir, mock_dataframe):
    """Test saving metrics to JSON."""
    schema = load_schema(temp_schema_dir)
    is_valid, metrics = validate_variables(mock_dataframe, schema)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = save_variable_metrics(metrics, Path(tmpdir))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['status'] == 'valid'
        assert saved_data['missing_count'] == 0


def test_detect_outliers_iqr():
    """Test outlier detection logic."""
    data = {
        'value': [1, 2, 3, 4, 5, 100]  # 100 is an obvious outlier
    }
    df = pd.DataFrame(data)
    
    result = detect_outliers_iqr(df, columns=['value'])
    
    assert 'is_outlier' in result.columns
    # The last row (100) should be flagged as outlier
    assert result.iloc[-1]['is_outlier'] is True
    # Others should be False
    assert result.iloc[0]['is_outlier'] is False


def test_filter_outliers():
    """Test filtering logic."""
    data = {
        'value': [1, 2, 3, 4, 5, 100],
        'id': [1, 2, 3, 4, 5, 6]
    }
    df = pd.DataFrame(data)
    # Manually set outlier for testing filter function directly
    df['is_outlier'] = [False, False, False, False, False, True]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "filtered.parquet"
        filtered_df = filter_outliers(df, output_path)
        
        assert len(filtered_df) == 5
        assert output_path.exists()
        assert 'is_outlier' not in filtered_df.columns or not filtered_df['is_outlier'].any()
