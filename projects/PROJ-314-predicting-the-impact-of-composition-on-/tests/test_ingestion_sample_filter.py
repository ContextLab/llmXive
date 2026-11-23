import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import filter_valid_sample_count

def test_filter_valid_sample_count_positive():
    """Test that rows with N >= 30 are kept."""
    data = {
        'composition': ['Al2O3', 'SiO2', 'ZrO2'],
        'N': [50, 30, 29],
        'weibull_modulus': [10.0, 12.0, 15.0]
    }
    df = pd.DataFrame(data)
    result = filter_valid_sample_count(df)
    
    assert len(result) == 2
    assert set(result['N'].values) == {50, 30}
    assert 'sample_count' in result.columns

def test_filter_valid_sample_count_missing_column():
    """Test behavior when no sample count column is found."""
    data = {
        'composition': ['Al2O3', 'SiO2'],
        'weibull_modulus': [10.0, 12.0]
    }
    df = pd.DataFrame(data)
    result = filter_valid_sample_count(df)
    
    assert len(result) == 0

def test_filter_valid_sample_count_non_numeric():
    """Test that non-numeric N values are excluded."""
    data = {
        'composition': ['Al2O3', 'SiO2', 'ZrO2'],
        'N': [50, 'unknown', 30],
        'weibull_modulus': [10.0, 12.0, 15.0]
    }
    df = pd.DataFrame(data)
    result = filter_valid_sample_count(df)
    
    assert len(result) == 2
    assert 'unknown' not in result['sample_count'].values

def test_filter_valid_sample_count_column_rename():
    """Test that 'N' is renamed to 'sample_count'."""
    data = {
        'composition': ['Al2O3'],
        'N': [100],
        'weibull_modulus': [10.0]
    }
    df = pd.DataFrame(data)
    result = filter_valid_sample_count(df)
    
    assert 'sample_count' in result.columns
    assert 'N' not in result.columns

def test_filter_valid_sample_count_output_file():
    """Test that the output file is created."""
    data = {
        'composition': ['Al2O3'],
        'N': [100],
        'weibull_modulus': [10.0]
    }
    df = pd.DataFrame(data)
    filter_valid_sample_count(df)
    
    output_path = Path("data/processed/step0_sample_count_filtered.csv")
    assert output_path.exists()
    output_path.unlink() # Cleanup
