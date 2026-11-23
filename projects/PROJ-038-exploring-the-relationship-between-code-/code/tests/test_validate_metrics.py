import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.validate_metrics import validate_no_nan_in_metrics, validate_schema_and_metrics

def test_validate_no_nan_in_metrics_pass():
    """Test that validation passes when no NaN values are present."""
    data = {
        'file_path': ['A.java', 'B.java'],
        'cc': [5, 10],
        'halstead': [100.5, 200.5],
        'loc': [50, 100],
        'is_buggy': [0, 1]
    }
    df = pd.DataFrame(data)
    is_valid, missing = validate_no_nan_in_metrics(df, ['cc', 'halstead', 'loc'])
    assert is_valid is True
    assert missing == []

def test_validate_no_nan_in_metrics_fail():
    """Test that validation fails when NaN values are present."""
    data = {
        'file_path': ['A.java', 'B.java'],
        'cc': [5, None],
        'halstead': [100.5, 200.5],
        'loc': [50, 100],
        'is_buggy': [0, 1]
    }
    df = pd.DataFrame(data)
    is_valid, missing = validate_no_nan_in_metrics(df, ['cc', 'halstead', 'loc'])
    assert is_valid is False
    assert 'cc' in missing

def test_validate_no_nan_in_metrics_missing_column():
    """Test that ValueError is raised if a metric column is missing."""
    data = {
        'file_path': ['A.java'],
        'cc': [5],
        'halstead': [100.5],
        # 'loc' is missing
        'is_buggy': [0]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="Required metric column 'loc' not found"):
        validate_no_nan_in_metrics(df, ['cc', 'halstead', 'loc'])

def test_validate_schema_and_metrics_pass():
    """Test full schema validation with valid data."""
    data = {
        'file_path': ['A.java'],
        'cc': [5],
        'halstead': [100.5],
        'loc': [50],
        'is_buggy': [0]
    }
    df = pd.DataFrame(data)
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_schema_and_metrics(df, Path(tmpdir) / "dummy.csv")
        assert result is True

def test_validate_schema_and_metrics_nan_fail():
    """Test full schema validation fails with NaN values."""
    data = {
        'file_path': ['A.java'],
        'cc': [None],
        'halstead': [100.5],
        'loc': [50],
        'is_buggy': [0]
    }
    df = pd.DataFrame(data)
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="NaN values found"):
            validate_schema_and_metrics(df, Path(tmpdir) / "dummy.csv")

def test_validate_schema_and_metrics_empty_df():
    """Test validation fails on empty DataFrame."""
    df = pd.DataFrame()
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="empty"):
            validate_schema_and_metrics(df, Path(tmpdir) / "dummy.csv")
