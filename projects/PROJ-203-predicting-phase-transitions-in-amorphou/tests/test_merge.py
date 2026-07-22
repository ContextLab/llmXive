"""
Tests for T013: Merge simulation descriptors with experimental labels.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.merge import (
    load_simulation_descriptors,
    load_experimental_labels,
    merge_datasets,
    save_merged_dataset,
    main
)
from config import get_paths

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_root = Path(tempfile.mkdtemp())
    raw_dir = temp_root / "data" / "raw"
    processed_dir = temp_root / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    yield {
        "raw": raw_dir,
        "processed": processed_dir,
        "root": temp_root
    }
    
    shutil.rmtree(temp_root)

@pytest.fixture
def mock_descriptors_df():
    """Create a mock descriptors DataFrame."""
    return pd.DataFrame({
        "composition_id": ["A", "B", "C", "D"],
        "rdf_peak_1": [1.2, 1.3, 1.4, 1.5],
        "bond_angle_var": [0.1, 0.2, 0.3, 0.4],
        "coordination_num": [4, 5, 6, 7]
    })

@pytest.fixture
def mock_experimental_df():
    """Create a mock experimental DataFrame."""
    return pd.DataFrame({
        "composition_id": ["A", "B", "C", "E"],
        "Tg": [500, 520, 480, 550],
        "Tx": [600, 610, 590, 650],
        "family": ["oxide", "sulfide", "organic", "oxide"]
    })

def test_load_experimental_labels_missing_file(temp_dirs):
    """Test that load_experimental_labels fails loudly when file is missing."""
    # Don't create the file
    with pytest.raises(FileNotFoundError) as exc_info:
        # Mock the paths to point to our temp dir
        with patch('data.merge.get_paths') as mock_paths:
            mock_paths.return_value.raw = temp_dirs["raw"]
            load_experimental_labels()
    
    assert "literature_subset.csv missing" in str(exc_info.value)

def test_load_experimental_labels_success(temp_dirs, mock_experimental_df):
    """Test successful loading of experimental labels."""
    literature_file = temp_dirs["raw"] / "literature_subset.csv"
    mock_experimental_df.to_csv(literature_file, index=False)
    
    with patch('data.merge.get_paths') as mock_paths:
        mock_paths.return_value.raw = temp_dirs["raw"]
        df = load_experimental_labels()
    
    assert len(df) == 4
    assert "composition_id" in df.columns
    assert "Tg" in df.columns

def test_merge_datasets_inner_join(mock_descriptors_df, mock_experimental_df):
    """Test that merge performs an inner join correctly."""
    merged = merge_datasets(mock_descriptors_df, mock_experimental_df)
    
    # Should only have A, B, C (intersection of both)
    assert len(merged) == 3
    assert set(merged["composition_id"]) == {"A", "B", "C"}
    
    # Should have columns from both
    assert "rdf_peak_1" in merged.columns
    assert "Tg" in merged.columns

def test_merge_datasets_key_error(mock_descriptors_df, mock_experimental_df):
    """Test that merge fails when key column is missing."""
    # Remove key column from descriptors
    bad_descriptors = mock_descriptors_df.drop(columns=["composition_id"])
    
    with pytest.raises(KeyError):
        merge_datasets(bad_descriptors, mock_experimental_df)

def test_save_merged_dataset(temp_dirs, mock_descriptors_df, mock_experimental_df):
    """Test saving merged dataset to Parquet."""
    merged = merge_datasets(mock_descriptors_df, mock_experimental_df)
    output_path = temp_dirs["processed"] / "test_output.parquet"
    
    saved_path = save_merged_dataset(merged, output_path)
    
    assert saved_path.exists()
    loaded = pd.read_parquet(saved_path)
    assert len(loaded) == 3

def test_main_integration(temp_dirs, mock_descriptors_df, mock_experimental_df):
    """Test the full main() pipeline with mocked data."""
    # Setup files
    literature_file = temp_dirs["raw"] / "literature_subset.csv"
    mock_experimental_df.to_csv(literature_file, index=False)
    
    # Create intermediate descriptors file
    intermediate_file = temp_dirs["processed"] / "intermediate_descriptors.parquet"
    mock_descriptors_df.to_parquet(intermediate_file)
    
    with patch('data.merge.get_paths') as mock_paths:
        mock_paths.return_value.raw = temp_dirs["raw"]
        mock_paths.return_value.processed = temp_dirs["processed"]
        
        result_path = main()
    
    assert result_path.exists()
    final_df = pd.read_parquet(result_path)
    assert len(final_df) == 3
    assert "Tg" in final_df.columns
    assert "rdf_peak_1" in final_df.columns

def test_empty_merged_result(temp_dirs):
    """Test handling when merge results in empty DataFrame."""
    descriptors = pd.DataFrame({"composition_id": ["X", "Y"], "val": [1, 2]})
    experimental = pd.DataFrame({"composition_id": ["A", "B"], "Tg": [500, 600]})
    
    with pytest.raises(RuntimeError) as exc_info:
        merge_datasets(descriptors, experimental)
    
    assert "Merged dataset is empty" in str(exc_info.value)