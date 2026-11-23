"""
Unit tests for ingest.py
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import clean_data, validate_tg_range, DataInsufficientError

def test_clean_data_removes_null_tg():
    """Test that clean_data removes rows with missing Tg."""
    df = pd.DataFrame({
        'Tg': [300.0, None, 400.0, None],
        'Composition': ['Cu-Zr', 'Al-Ni', 'Fe-B', 'Ti-Cu']
    })
    
    df_clean, raw, cleaned = clean_data(df, None)
    
    assert len(df_clean) == 2
    assert raw == 4
    assert cleaned == 2
    assert df_clean['Tg'].isna().sum() == 0

def test_clean_data_removes_null_composition():
    """Test that clean_data removes rows with missing composition."""
    df = pd.DataFrame({
        'Tg': [300.0, 400.0, 500.0],
        'Composition': ['Cu-Zr', None, 'Fe-B']
    })
    
    df_clean, raw, cleaned = clean_data(df, None)
    
    assert len(df_clean) == 2
    assert raw == 3
    assert cleaned == 2
    assert df_clean['Composition'].isna().sum() == 0

def test_clean_data_empty_result_raises_error():
    """Test that clean_data raises DataInsufficientError if all rows are dropped."""
    df = pd.DataFrame({
        'Tg': [None, None],
        'Composition': ['Cu-Zr', 'Al-Ni']
    })
    
    with pytest.raises(DataInsufficientError):
        clean_data(df, None)

def test_validate_tg_range():
    """Test Tg range validation."""
    df = pd.DataFrame({
        'Tg': [100.0, 500.0, 2500.0, 50.0]
    })
    
    df_valid = validate_tg_range(df, min_tg=100.0, max_tg=2000.0)
    
    assert len(df_valid) == 2
    assert 500.0 in df_valid['Tg'].values
    assert 100.0 in df_valid['Tg'].values