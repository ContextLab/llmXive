"""
Tests for T014: Save final processed dataset.

These tests verify that the final dataset is saved correctly with all required metadata.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.save_final_dataset import load_simulation_metadata, save_final_dataset
from config import get_config

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'composition_id': ['comp_001', 'comp_002', 'comp_003'],
        'Tg_exp': [500, 520, 480],
        'crystallization_label': [0, 1, 0],
        'rdf_peak_1': [2.5, 2.6, 2.4],
        'bond_angle_var': [0.1, 0.15, 0.12]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        'SRO_Invariance_Assumed': False,
        'cooling_rate_scaling_factor': 1.5,
        'truncated_compositions': ['comp_002'],
        'failed_compositions': []
    }

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_simulation_metadata_defaults(temp_output_dir):
    """Test that load_simulation_metadata returns default values when no files exist."""
    # Create a mock config object
    class MockConfig:
        class data:
            processed_dir = str(temp_output_dir)
            logs_dir = str(temp_output_dir)
    
    metadata = load_simulation_metadata(MockConfig())
    
    assert metadata['SRO_Invariance_Assumed'] is False
    assert metadata['cooling_rate_scaling_factor'] is None
    assert metadata['truncated_compositions'] == []
    assert metadata['failed_compositions'] == []

def test_save_final_dataset_creates_file(sample_dataframe, sample_metadata, temp_output_dir):
    """Test that save_final_dataset creates the Parquet file."""
    output_path = temp_output_dir / "test_output.parquet"
    
    save_final_dataset(sample_dataframe, sample_metadata, output_path)
    
    assert output_path.exists()
    
    # Verify the file can be read back
    df = pd.read_parquet(output_path)
    assert len(df) == len(sample_dataframe)
    assert 'composition_id' in df.columns
    assert 'Tg_exp' in df.columns

def test_save_final_dataset_preserves_data(sample_dataframe, sample_metadata, temp_output_dir):
    """Test that save_final_dataset preserves all data."""
    output_path = temp_output_dir / "test_output.parquet"
    
    save_final_dataset(sample_dataframe, sample_metadata, output_path)
    
    df = pd.read_parquet(output_path)
    
    # Check all rows are preserved
    assert len(df) == len(sample_dataframe)
    
    # Check all columns are preserved
    for col in sample_dataframe.columns:
        assert col in df.columns
        np.testing.assert_array_equal(df[col].values, sample_dataframe[col].values)

def test_save_final_dataset_adds_flags(sample_dataframe, sample_metadata, temp_output_dir):
    """Test that save_final_dataset adds truncation and failure flags."""
    output_path = temp_output_dir / "test_output.parquet"
    
    save_final_dataset(sample_dataframe, sample_metadata, output_path)
    
    df = pd.read_parquet(output_path)
    
    # Check that flag columns were added
    assert 'is_truncated' in df.columns
    assert 'is_failed' in df.columns
    
    # Verify the flags are correct
    assert df.loc[df['composition_id'] == 'comp_002', 'is_truncated'].iloc[0] is True
    assert df.loc[df['composition_id'] == 'comp_001', 'is_truncated'].iloc[0] is False

def test_save_final_dataset_with_empty_metadata(sample_dataframe, temp_output_dir):
    """Test saving with minimal metadata."""
    metadata = {
        'SRO_Invariance_Assumed': False,
        'cooling_rate_scaling_factor': None,
        'truncated_compositions': [],
        'failed_compositions': []
    }
    
    output_path = temp_output_dir / "test_output.parquet"
    
    save_final_dataset(sample_dataframe, metadata, output_path)
    
    assert output_path.exists()
    df = pd.read_parquet(output_path)
    assert len(df) == len(sample_dataframe)

def test_save_final_dataset_creates_parent_directory(sample_dataframe, sample_metadata, temp_output_dir):
    """Test that save_final_dataset creates parent directories if they don't exist."""
    output_path = temp_output_dir / "subdir" / "nested" / "test_output.parquet"
    
    # Parent directories don't exist yet
    assert not output_path.parent.exists()
    
    save_final_dataset(sample_dataframe, sample_metadata, output_path)
    
    assert output_path.exists()
    assert output_path.parent.exists()
