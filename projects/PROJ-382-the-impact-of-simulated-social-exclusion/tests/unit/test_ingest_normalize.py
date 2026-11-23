"""
Unit tests for the column normalizer in code/ingest.py (T013).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Import the function to test
# Since ingest.py imports config and logging, we might need to mock them or ensure they exist.
# For unit testing, we can try to import directly. If dependencies are heavy, we might mock.
# However, the task requires real code. We assume the environment is set up.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest import normalize_columns

def test_normalize_prosocial_column_variants():
    """Test that various column names for prosocial amount are mapped correctly."""
    variants = ['donation', 'allocation', 'transfer', 'giving', 'prosocial_amount']
    for variant in variants:
        df = pd.DataFrame({
            variant: [10, 20, 30],
            'condition': ['control', 'excluded', 'control'],
            'randomized': [True, True, False]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'mapping_log.json'
            result = normalize_columns(df, f"test_{variant}", log_path)
            
            assert 'prosocial_amount' in result.columns
            assert list(result['prosocial_amount']) == [10, 20, 30]
            assert variant not in result.columns or variant == 'prosocial_amount'

def test_normalize_condition_strings_to_int():
    """Test that condition strings are mapped to 1 (exclusion) and 0 (control)."""
    df = pd.DataFrame({
        'prosocial_amount': [10, 20, 30, 40],
        'condition': ['excluded', 'ignored', 'control', 'included'],
        'randomized': [True, True, True, True]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'mapping_log.json'
        result = normalize_columns(df, "test_condition", log_path)
        
        # Check that condition column is now numeric (1 for exclusion, 0 for control)
        assert list(result['condition']) == [1, 1, 0, 0]

def test_normalize_randomized_column():
    """Test that randomized column is normalized to boolean."""
    df = pd.DataFrame({
        'prosocial_amount': [10, 20, 30],
        'condition': ['excluded', 'control', 'excluded'],
        'randomized': ['yes', 'no', 1, 0] # Mixed types
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'mapping_log.json'
        result = normalize_columns(df, "test_randomized", log_path)
        
        # Check that randomized is boolean
        assert result['randomized'].dtype == bool
        assert list(result['randomized']) == [True, False, True, False]

def test_missing_randomized_defaults_to_false():
    """Test that missing 'randomized' column defaults to False."""
    df = pd.DataFrame({
        'prosocial_amount': [10, 20],
        'condition': ['excluded', 'control']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'mapping_log.json'
        result = normalize_columns(df, "test_missing_randomized", log_path)
        
        assert 'randomized' in result.columns
        assert all(result['randomized'] == False)

def test_mapping_log_created():
    """Test that mapping log is created and contains records."""
    df = pd.DataFrame({
        'donation': [10, 20],
        'condition': ['excluded', 'control'],
        'randomized': [True, False]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'mapping_log.json'
        result = normalize_columns(df, "test_log", log_path)
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) > 0
        # Check for column rename record
        rename_records = [l for l in logs if l.get('mapping_type') == 'column_rename']
        assert len(rename_records) > 0
        assert rename_records[0]['original_column'] == 'donation'
        assert rename_records[0]['target_column'] == 'prosocial_amount'

def test_unknown_condition_values_become_nan():
    """Test that unknown condition values are mapped to NaN."""
    df = pd.DataFrame({
        'prosocial_amount': [10, 20, 30],
        'condition': ['excluded', 'unknown_condition', 'control'],
        'randomized': [True, True, True]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'mapping_log.json'
        result = normalize_columns(df, "test_unknown", log_path)
        
        # Check that unknown condition is NaN
        assert pd.isna(result['condition'].iloc[1])
        assert result['condition'].iloc[0] == 1
        assert result['condition'].iloc[2] == 0
