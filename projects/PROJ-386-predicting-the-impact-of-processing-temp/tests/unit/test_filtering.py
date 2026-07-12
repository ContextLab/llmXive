import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data.ingestion import filter_data

def test_filter_null_temperature():
    """Test that rows with null temperature are excluded."""
    data = [
        {
            'data': [
                {'rolling_temperature': 500.0, 'grain_size': 10.0, 'mg': 1.0},
                {'rolling_temperature': None, 'grain_size': 12.0, 'mg': 1.2},
                {'rolling_temperature': 550.0, 'grain_size': 8.0, 'mg': 1.1}
            ]
        }
    ]
    
    result = filter_data(data)
    
    assert len(result) == 2
    assert result['rolling_temperature'].isna().sum() == 0
    assert 500.0 in result['rolling_temperature'].values
    assert 550.0 in result['rolling_temperature'].values

def test_filter_null_grain_size():
    """Test that rows with null grain size are excluded."""
    data = [
        {
            'data': [
                {'rolling_temperature': 500.0, 'grain_size': 10.0, 'mg': 1.0},
                {'rolling_temperature': 510.0, 'grain_size': None, 'mg': 1.1},
                {'rolling_temperature': 520.0, 'grain_size': 9.5, 'mg': 1.3}
            ]
        }
    ]
    
    result = filter_data(data)
    
    assert len(result) == 2
    assert result['grain_size'].isna().sum() == 0

def test_filter_null_composition():
    """Test that rows with null composition (at least one element) are excluded."""
    data = [
        {
            'data': [
                {'rolling_temperature': 500.0, 'grain_size': 10.0, 'mg': 1.0},
                {'rolling_temperature': 510.0, 'grain_size': 11.0, 'mg': None},
                {'rolling_temperature': 520.0, 'grain_size': 12.0, 'mg': 1.5}
            ]
        }
    ]
    
    result = filter_data(data)
    
    assert len(result) == 2
    assert result['mg'].isna().sum() == 0

def test_filter_all_null_critical():
    """Test that if all rows have null critical variables, result is empty."""
    data = [
        {
            'data': [
                {'rolling_temperature': None, 'grain_size': 10.0, 'mg': 1.0},
                {'rolling_temperature': 500.0, 'grain_size': None, 'mg': 1.0},
                {'rolling_temperature': 500.0, 'grain_size': 10.0, 'mg': None}
            ]
        }
    ]
    
    result = filter_data(data)
    assert len(result) == 0

def test_case_insensitive_columns():
    """Test that column name variations (case insensitive) are handled."""
    data = [
        {
            'data': [
                {'Rolling_Temperature': 500.0, 'Grain_Size': 10.0, 'Mg': 1.0},
                {'Rolling_Temperature': 510.0, 'Grain_Size': 11.0, 'Mg': 1.1}
            ]
        }
    ]
    
    result = filter_data(data)
    assert len(result) == 2
    # Columns should be lowercased
    assert 'rolling_temperature' in result.columns
    assert 'grain_size' in result.columns
    assert 'mg' in result.columns

def test_final_size_report():
    """Verify that filtering reduces the dataset size as expected."""
    initial_rows = 100
    null_rows = 20
    valid_rows = initial_rows - null_rows
    
    # Create synthetic data
    rows = []
    for i in range(initial_rows):
        if i < null_rows:
            rows.append({'rolling_temperature': None, 'grain_size': 10.0, 'mg': 1.0})
        else:
            rows.append({'rolling_temperature': 500.0 + i, 'grain_size': 10.0, 'mg': 1.0})
    
    data = [{'data': rows}]
    result = filter_data(data)
    
    assert len(result) == valid_rows