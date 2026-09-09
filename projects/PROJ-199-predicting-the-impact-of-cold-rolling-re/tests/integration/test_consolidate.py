"""
Integration tests for the data consolidation pipeline (Task T015).
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.consolidate import load_all_processed_datasets, write_consolidated_parquet, main
from code.utils.logging import setup_logging

@pytest.fixture
def temp_interim_dir():
    """Create a temporary directory structure mimicking the project's data/interim."""
    temp_dir = tempfile.mkdtemp()
    interim_path = Path(temp_dir) / "interim"
    interim_path.mkdir()
    return interim_path

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for output."""
    temp_dir = tempfile.mkdtemp()
    processed_path = Path(temp_dir) / "processed"
    processed_path.mkdir()
    return processed_path

def test_load_all_processed_datasets_success(temp_interim_dir):
    """Test successful loading of multiple parquet files."""
    # Create mock data
    df1 = pd.DataFrame({
        'material': ['Al', 'Al'],
        'reduction': [20, 40],
        'confidence': [0.9, 0.8],
        'euler1': [10.0, 20.0],
        'euler2': [30.0, 40.0],
        'euler3': [50.0, 60.0]
    })
    df2 = pd.DataFrame({
        'material': ['Cu'],
        'reduction': [60],
        'confidence': [0.95],
        'euler1': [15.0],
        'euler2': [35.0],
        'euler3': [55.0]
    })

    df1.to_parquet(temp_interim_dir / "al_data.parquet")
    df2.to_parquet(temp_interim_dir / "cu_data.parquet")

    # Mock the global INTERIM_DIR for the test
    import code.data.consolidate as consolidate_module
    original_interim = consolidate_module.INTERIM_DIR
    consolidate_module.INTERIM_DIR = temp_interim_dir

    try:
        result = load_all_processed_datasets()
        assert len(result) == 3
        assert set(result['material'].unique()) == {'Al', 'Cu'}
        assert list(result.columns) == ['material', 'reduction', 'confidence', 'euler1', 'euler2', 'euler3']
    finally:
        consolidate_module.INTERIM_DIR = original_interim

def test_load_all_processed_datasets_empty_dir(temp_interim_dir):
    """Test error when no parquet files exist."""
    import code.data.consolidate as consolidate_module
    original_interim = consolidate_module.INTERIM_DIR
    consolidate_module.INTERIM_DIR = temp_interim_dir

    try:
        with pytest.raises(FileNotFoundError):
            load_all_processed_datasets()
    finally:
        consolidate_module.INTERIM_DIR = original_interim

def test_load_all_processed_datasets_missing_columns(temp_interim_dir):
    """Test skipping files with missing required columns."""
    # File with required columns
    df_valid = pd.DataFrame({
        'material': ['Al'],
        'reduction': [20],
        'confidence': [0.9],
        'euler1': [10.0],
        'euler2': [30.0],
        'euler3': [50.0]
    })
    # File missing 'confidence'
    df_invalid = pd.DataFrame({
        'material': ['Cu'],
        'reduction': [60],
        'euler1': [15.0],
        'euler2': [35.0],
        'euler3': [55.0]
    })

    df_valid.to_parquet(temp_interim_dir / "valid.parquet")
    df_invalid.to_parquet(temp_interim_dir / "invalid.parquet")

    import code.data.consolidate as consolidate_module
    original_interim = consolidate_module.INTERIM_DIR
    consolidate_module.INTERIM_DIR = temp_interim_dir

    try:
        result = load_all_processed_datasets()
        # Should only load the valid file
        assert len(result) == 1
        assert result['material'].iloc[0] == 'Al'
    finally:
        consolidate_module.INTERIM_DIR = original_interim

def test_write_consolidated_parquet_success(temp_interim_dir, temp_processed_dir):
    """Test successful writing of consolidated parquet."""
    df = pd.DataFrame({
        'material': ['Al', 'Cu'],
        'reduction': [20, 60],
        'confidence': [0.9, 0.95],
        'euler1': [10.0, 15.0],
        'euler2': [30.0, 35.0],
        'euler3': [50.0, 55.0]
    })

    output_path = temp_processed_dir / "cleaned_ebsd.parquet"
    result_path = write_consolidated_parquet(df, output_path)

    assert result_path.exists()
    loaded_df = pd.read_parquet(result_path)
    assert len(loaded_df) == 2
    assert 'material' in loaded_df.columns
    assert 'reduction' in loaded_df.columns
    assert 'confidence' in loaded_df.columns

def test_write_consolidated_parquet_empty_dataframe(temp_processed_dir):
    """Test error when writing empty dataframe (T015 Zero-Data Handling)."""
    df = pd.DataFrame(columns=['material', 'reduction', 'confidence'])
    output_path = temp_processed_dir / "cleaned_ebsd.parquet"

    with pytest.raises(ValueError, match="Cannot write empty dataset"):
        write_consolidated_parquet(df, output_path)

def test_main_success(temp_interim_dir, temp_processed_dir, caplog):
    """Test the main function execution flow."""
    # Setup mock data
    df = pd.DataFrame({
        'material': ['Al'],
        'reduction': [20],
        'confidence': [0.9],
        'euler1': [10.0],
        'euler2': [30.0],
        'euler3': [50.0]
    })
    df.to_parquet(temp_interim_dir / "test.parquet")

    # Mock paths
    import code.data.consolidate as consolidate_module
    original_interim = consolidate_module.INTERIM_DIR
    original_processed = consolidate_module.PROCESSED_DIR
    original_output = consolidate_module.OUTPUT_FILE

    consolidate_module.INTERIM_DIR = temp_interim_dir
    consolidate_module.PROCESSED_DIR = temp_processed_dir
    consolidate_module.OUTPUT_FILE = temp_processed_dir / "cleaned_ebsd.parquet"

    try:
        result = main()
        assert result == 0
        assert (consolidate_module.PROCESSED_DIR / "cleaned_ebsd.parquet").exists()
    finally:
        consolidate_module.INTERIM_DIR = original_interim
        consolidate_module.PROCESSED_DIR = original_processed
        consolidate_module.OUTPUT_FILE = original_output

def test_main_no_files(temp_interim_dir):
    """Test main function when no input files exist."""
    import code.data.consolidate as consolidate_module
    original_interim = consolidate_module.INTERIM_DIR
    consolidate_module.INTERIM_DIR = temp_interim_dir

    try:
        result = main()
        assert result == 1
    finally:
        consolidate_module.INTERIM_DIR = original_interim
