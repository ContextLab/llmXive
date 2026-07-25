"""
Unit tests for the data cleaning module.
"""
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from src.data.clean import clean_elastic_data
from src.utils.config import get_path

# Configure logger for tests
logger = logging.getLogger("test_clean")
logger.setLevel(logging.DEBUG)

@pytest.fixture
def sample_fcc_data():
    """Create a sample DataFrame mimicking ingested elastic data."""
    data = {
        'material_id': ['MP-123', 'MP-456', 'MP-789', 'MP-101', 'MP-102'],
        'formula': ['Al', 'Cu', 'Fe', 'Ni', 'Ag'],
        'crystal_system': ['cubic', 'cubic', 'cubic', 'tetragonal', 'cubic'],
        'C11': [100.0, 168.0, 226.0, 180.0, 90.0],
        'C12': [50.0, 121.0, 140.0, 140.0, 80.0],
        'C44': [28.0, 75.0, 116.0, 90.0, 40.0],
        'structure': [
            {'symmetry': {'crystal_system': 'cubic'}},
            {'symmetry': {'crystal_system': 'cubic'}},
            {'symmetry': {'crystal_system': 'cubic'}},
            {'symmetry': {'crystal_system': 'tetragonal'}},
            {'symmetry': {'crystal_system': 'cubic'}}
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_fcc_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_fcc_data.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_clean_fcc_filter(sample_fcc_data, temp_csv_file, temp_output_dir):
    """Test that non-cubic entries are filtered out."""
    output_path = os.path.join(temp_output_dir, "cleaned.csv")
    
    df_clean = clean_elastic_data(
        input_path=temp_csv_file,
        output_path=output_path,
        force_cubic=True
    )
    
    # Check that tetragonal entry (MP-101) is removed
    assert 'MP-101' not in df_clean['material_id'].values
    # Check that cubic entries remain
    assert len(df_clean) == 4
    assert all(df_clean['crystal_system'] == 'cubic')

def test_clean_division_by_zero(temp_output_dir):
    """Test that entries where C11 == C12 are removed."""
    data = {
        'material_id': ['MP-OK', 'MP-ZERO'],
        'crystal_system': ['cubic', 'cubic'],
        'C11': [100.0, 50.0],
        'C12': [50.0, 50.0],  # C11 == C12 for MP-ZERO
        'C44': [20.0, 30.0]
    }
    df_input = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df_input.to_csv(f, index=False)
        input_path = f.name
    
    output_path = os.path.join(temp_output_dir, "cleaned.csv")
    
    df_clean = clean_elastic_data(input_path=input_path, output_path=output_path)
    
    assert 'MP-ZERO' not in df_clean['material_id'].values
    assert len(df_clean) == 1
    assert 'MP-OK' in df_clean['material_id'].values

def test_clean_a1_calculation(temp_output_dir):
    """Test that A1 is calculated correctly."""
    # A1 = 2*C44 / (C11 - C12)
    # Example: C11=100, C12=50, C44=28 -> A1 = 56 / 50 = 1.12
    data = {
        'material_id': ['MP-CALC'],
        'crystal_system': ['cubic'],
        'C11': [100.0],
        'C12': [50.0],
        'C44': [28.0]
    }
    df_input = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df_input.to_csv(f, index=False)
        input_path = f.name
    
    output_path = os.path.join(temp_output_dir, "cleaned.csv")
    
    df_clean = clean_elastic_data(input_path=input_path, output_path=output_path)
    
    expected_a1 = (2 * 28.0) / (100.0 - 50.0)
    assert abs(df_clean['A1'].iloc[0] - expected_a1) < 1e-6

def test_clean_missing_columns_raises(temp_output_dir):
    """Test that missing required columns raise an error."""
    data = {
        'material_id': ['MP-NO-COLS'],
        'crystal_system': ['cubic'],
        'C11': [100.0]
        # Missing C12 and C44
    }
    df_input = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df_input.to_csv(f, index=False)
        input_path = f.name
    
    output_path = os.path.join(temp_output_dir, "cleaned.csv")
    
    with pytest.raises(ValueError):
        clean_elastic_data(input_path=input_path, output_path=output_path)

def test_clean_handles_nan_values(temp_output_dir):
    """Test that rows with NaN in elastic constants are dropped."""
    data = {
        'material_id': ['MP-NaN', 'MP-OK'],
        'crystal_system': ['cubic', 'cubic'],
        'C11': [100.0, np.nan],
        'C12': [50.0, 50.0],
        'C44': [28.0, 28.0]
    }
    df_input = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df_input.to_csv(f, index=False)
        input_path = f.name
    
    output_path = os.path.join(temp_output_dir, "cleaned.csv")
    
    df_clean = clean_elastic_data(input_path=input_path, output_path=output_path)
    
    assert 'MP-NaN' not in df_clean['material_id'].values
    assert len(df_clean) == 1

def test_clean_output_file_created(sample_fcc_data, temp_csv_file, temp_output_dir):
    """Test that the output file is actually created on disk."""
    output_path = os.path.join(temp_output_dir, "cleaned.csv")
    
    clean_elastic_data(input_path=temp_csv_file, output_path=output_path)
    
    assert os.path.exists(output_path)
    assert Path(output_path).stat().st_size > 0