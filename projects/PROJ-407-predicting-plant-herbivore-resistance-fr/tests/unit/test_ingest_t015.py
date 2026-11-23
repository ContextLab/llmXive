import pytest
import os
import json
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import (
    convert_categorical_to_ordinal,
    check_herbivore_density_normalization,
    harmonize_dataset,
    save_harmonized_dataset
)
from config import DATA_ROOT

def test_convert_categorical_to_ordinal():
    """Test categorical to ordinal conversion and log creation."""
    data = {
        'resistance': ['Low', 'Medium', 'High', 'Low'],
        'metabolite_A': [1.0, 2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    
    # Create a temporary directory for the test to avoid writing to real DATA_ROOT
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock DATA_ROOT
        import ingest
        original_root = ingest.DATA_ROOT
        ingest.DATA_ROOT = tmpdir
        
        try:
            result_df = convert_categorical_to_ordinal(df)
            
            assert 'resistance_ordinal' in result_df.columns
            assert result_df['resistance_ordinal'].tolist() == [1, 2, 3, 1]
            
            # Check log file
            log_path = os.path.join(tmpdir, 'interim', 'ordinal_mapping.log')
            assert os.path.exists(log_path)
            
            with open(log_path, 'r') as f:
                mapping = json.load(f)
            assert mapping == {"Low": 1, "Medium": 2, "High": 3}
        finally:
            ingest.DATA_ROOT = original_root

def test_check_herbivore_density_normalization_missing():
    """Test that missing herbivore_density updates metadata."""
    data = {
        'resistance': [1.0, 2.0],
        'metabolite_A': [1.0, 2.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        import ingest
        original_root = ingest.DATA_ROOT
        ingest.DATA_ROOT = tmpdir
        
        try:
            result_df = check_herbivore_density_normalization(df)
            
            metadata_path = os.path.join(tmpdir, 'interim', 'metadata.json')
            assert os.path.exists(metadata_path)
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            assert metadata.get('herbivore_density_missing') is True
        finally:
            ingest.DATA_ROOT = original_root

def test_check_herbivore_density_normalization_present():
    """Test that present herbivore_density updates metadata."""
    data = {
        'resistance': [1.0, 2.0],
        'herbivore_density': [10, 20],
        'metabolite_A': [1.0, 2.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        import ingest
        original_root = ingest.DATA_ROOT
        ingest.DATA_ROOT = tmpdir
        
        try:
            result_df = check_herbivore_density_normalization(df)
            
            metadata_path = os.path.join(tmpdir, 'interim', 'metadata.json')
            assert os.path.exists(metadata_path)
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            assert metadata.get('herbivore_density_missing') is False
        finally:
            ingest.DATA_ROOT = original_root

def test_harmonize_dataset_imputation_flag():
    """Test that harmonize_dataset creates imputation_flag correctly."""
    data = {
        'resistance': [1.0, 2.0, 3.0, 4.0],
        'metabolite_A': [1.0, None, 3.0, 4.0],
        'metabolite_B': [1.0, 2.0, 3.0, None]
    }
    df = pd.DataFrame(data)
    
    result_df = harmonize_dataset(df)
    
    assert 'imputation_flag' in result_df.columns
    # Row 1 has missing A -> True
    # Row 3 has missing B -> True
    # Row 0 and 2 have no missing -> False
    expected_flags = [False, True, False, True]
    assert result_df['imputation_flag'].tolist() == expected_flags

def test_harmonize_dataset_drops_missing_resistance():
    """Test that rows with missing resistance are dropped."""
    data = {
        'resistance': [1.0, None, 3.0],
        'metabolite_A': [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    result_df = harmonize_dataset(df)
    
    assert len(result_df) == 2
    assert result_df['resistance'].isna().sum() == 0