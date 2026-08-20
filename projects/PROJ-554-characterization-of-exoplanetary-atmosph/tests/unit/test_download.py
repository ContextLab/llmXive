"""
Unit tests for download module functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from download import classify_planet_category, count_unique_planets, process_metadata

@pytest.fixture
def sample_metadata_df():
    """Create a sample metadata DataFrame for testing."""
    data = {
        'pl_name': ['Planet A', 'Planet B', 'Planet C'],
        'equilibrium_temperature': [1500.0, 800.0, 1200.0],
        'radius': [1.2, 1.5, 0.9],  # In Jupiter radii
        'mass': [1.0, 0.5, 0.8],
        'metallicity': [0.1, 0.2, 0.15],
        'snr': [10.0, 5.0, 8.0],
        'resolution': [50, 30, 40]
    }
    return pd.DataFrame(data)

def test_classify_hot_jupiter():
    """Test classification of Hot Jupiter."""
    row = pd.Series({
        'equilibrium_temperature': 1500.0,
        'radius': 1.2  # ~13.4 R_E
    })
    category = classify_planet_category(row)
    assert category == 'Hot Jupiter'

def test_classify_temperate_super_earth():
    """Test classification of Temperate Super-Earth."""
    row = pd.Series({
        'equilibrium_temperature': 800.0,
        'radius': 0.5  # ~5.6 R_E
    })
    category = classify_planet_category(row)
    assert category == 'Temperate Super-Earth'

def test_classify_unknown():
    """Test classification with missing values."""
    row = pd.Series({
        'equilibrium_temperature': np.nan,
        'radius': 1.0
    })
    category = classify_planet_category(row)
    assert category == 'Unknown'

def test_count_unique_planets():
    """Test counting unique planets from metadata file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample metadata file
        metadata_path = Path(tmpdir) / 'metadata.csv'
        data = {
            'planet_name': ['Planet A', 'Planet B', 'Planet C', 'Planet A'],  # Duplicate
            'temperature': [1000, 800, 1200, 1000],
            'metallicity': [0.1, 0.2, 0.15, 0.1],
            'snr': [10, 5, 8, 10],
            'resolution': [50, 30, 40, 50],
            'planet_category': ['Hot Jupiter', 'Temperate Super-Earth', 'Hot Jupiter', 'Hot Jupiter'],
            'instrument': ['HST', 'HST', 'HST', 'HST'],
            'wavelength_range': ['1.1-1.7', '1.1-1.7', '1.1-1.7', '1.1-1.7']
        }
        pd.DataFrame(data).to_csv(metadata_path, index=False)
        
        # Test count function
        result = count_unique_planets(metadata_path)
        
        assert 'count' in result
        assert result['count'] == 3  # 3 unique planets
        assert result['source_file'] == str(metadata_path)

def test_count_unique_planets_file_not_found():
    """Test count function with non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / 'nonexistent.csv'
        
        with pytest.raises(FileNotFoundError):
            count_unique_planets(metadata_path)

def test_process_metadata_column_mapping():
    """Test that process_metadata correctly maps columns."""
    raw_data = {
        'pl_name': ['Test Planet'],
        'pl_radj': [1.0],
        'pl_eqt': [1000.0],
        'pl_massj': [1.0],
        'st_met': [0.1],
        'snr': [10.0],
        'resolution': [50]
    }
    raw_df = pd.DataFrame(raw_data)
    
    processed_df = process_metadata(raw_df)
    
    assert 'planet_name' in processed_df.columns
    assert 'radius' in processed_df.columns
    assert 'equilibrium_temperature' in processed_df.columns
    assert 'mass' in processed_df.columns
    assert 'metallicity' in processed_df.columns
    assert 'planet_category' in processed_df.columns

def test_process_metadata_adds_category():
    """Test that process_metadata adds planet_category column."""
    raw_data = {
        'pl_name': ['Test Planet'],
        'pl_radj': [1.2],  # Hot Jupiter
        'pl_eqt': [1500.0],
        'pl_massj': [1.0],
        'st_met': [0.1],
        'snr': [10.0],
        'resolution': [50]
    }
    raw_df = pd.DataFrame(raw_data)
    
    processed_df = process_metadata(raw_df)
    
    assert processed_df['planet_category'].iloc[0] == 'Hot Jupiter'