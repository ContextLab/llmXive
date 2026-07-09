import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_ingestion import filter_and_impute, save_processed_data, validate_rotation_period
from config import DEFAULT_M_DWARF_AGE

def test_filter_and_impute_m_dwarf():
    """Test that non-M-dwarfs are filtered out."""
    data = {
        'spectral_type': ['M', 'K', 'M', 'G'],
        'flare_count': [15, 20, 5, 12],
        'mass': [0.5, 0.8, 0.4, 1.0],
        'radius': [0.5, 0.7, 0.4, 1.0],
        'semi_major_axis': [0.1, 0.5, 0.1, 1.0],
        'system_age': [4.0, 5.0, 3.0, 6.0]
    }
    df = pd.DataFrame(data)
    result = filter_and_impute(df)
    
    # Should only keep M-dwarfs with flare_count >= 10
    assert len(result) == 1
    assert result.iloc[0]['spectral_type'] == 'M'
    assert result.iloc[0]['flare_count'] == 15

def test_filter_and_impute_missing_age():
    """Test imputation of missing system_age."""
    data = {
        'spectral_type': ['M', 'M'],
        'flare_count': [15, 20],
        'mass': [0.5, 0.4],
        'radius': [0.5, 0.4],
        'semi_major_axis': [0.1, 0.1],
        'system_age': [4.0, None]
    }
    df = pd.DataFrame(data)
    result = filter_and_impute(df)
    
    assert result['system_age'].iloc[1] == DEFAULT_M_DWARF_AGE

def test_validate_rotation_period_missing():
    """Test warning and flag when Rotation Period is missing."""
    data = {
        'host_id': [1, 2],
        'mass': [0.5, 0.4],
        'radius': [0.5, 0.4],
        'semi_major_axis': [0.1, 0.1]
    }
    df = pd.DataFrame(data)
    result = validate_rotation_period(df)
    
    assert 'rotation_period_missing' in result.columns
    assert result['rotation_period_missing'].all()

def test_save_processed_data_creates_file(tmp_path):
    """Test that save_processed_data creates the file and returns checksum."""
    data = {
        'host_id': [1],
        'flare_count': [15],
        'mass': [0.5],
        'radius': [0.5],
        'semi_major_axis': [0.1],
        'system_age': [4.0]
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "test_output.csv"
    
    checksum = save_processed_data(df, str(output_path))
    
    assert output_path.exists()
    assert len(checksum) == 64  # SHA-256 hex length