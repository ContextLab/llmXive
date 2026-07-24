"""
Unit tests for the consolidate_data module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock the config and utils to avoid dependency on full setup during unit tests
# In a real integration, these would be real modules.
# We will test the logic functions directly.

from consolidate_data import load_processed_data, save_consolidated_data

def test_save_consolidated_data_creates_file():
    """Test that save_consolidated_data creates the file and logs checksum."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_file = tmp_path / "test_output.parquet"
        checksum_log = tmp_path / "checksums.json"
        
        # Create dummy data
        df = pd.DataFrame({
            'material_id': ['mp-1', 'mp-2'],
            'property_val': [1.0, 2.0],
            'magpie_feature': [0.5, 0.6]
        })
        
        # Save
        save_consolidated_data(df, output_file, checksum_log)
        
        # Assertions
        assert output_file.exists(), "Output parquet file was not created."
        assert checksum_log.exists(), "Checksum log was not created."
        
        # Verify content
        loaded_df = pd.read_parquet(output_file)
        assert len(loaded_df) == 2
        assert 'material_id' in loaded_df.columns

def test_load_processed_data_returns_none_if_missing():
    """Test that load_processed_data returns None for missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # No files created
        result = load_processed_data(Path(tmpdir), "nonexistent_property")
        assert result is None

def test_load_processed_data_loads_correctly():
    """Test loading a valid parquet file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        # Create a dummy file
        dummy_file = processed_dir / "processed_test_prop.parquet"
        df_dummy = pd.DataFrame({'col1': [1, 2, 3]})
        df_dummy.to_parquet(dummy_file)
        
        # Load
        result = load_processed_data(tmp_path, "test_prop")
        
        assert result is not None
        assert len(result) == 3
        assert 'col1' in result.columns