"""
Unit tests for data loading and schema validation in ingest.py
"""
import pytest
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure we can import from code/
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingest import setup_logging, setup_directories, load_and_align_data

def test_setup_directories_creates_paths(tmp_path):
    """Test that setup_directories creates the required directory structure."""
    # Mock the arguments to use the temporary directory
    import argparse
    args = argparse.Namespace(
        data_dir=str(tmp_path / "data"),
        results_dir=str(tmp_path / "results")
    )
    
    # This should not raise an exception
    setup_directories(args)
    
    # Verify directories exist
    assert (tmp_path / "data").exists()
    assert (tmp_path / "data" / "raw").exists()
    assert (tmp_path / "data" / "processed").exists()
    assert (tmp_path / "results").exists()

def test_load_and_align_data_with_mock_file(tmp_path):
    """Test loading and aligning data from a mock parquet file."""
    # Create a mock dataset
    mock_data = {
        'prompt': ['test prompt 1', 'test prompt 2'],
        'image_url': ['url1', 'url2'],
        'teacher_scores': [
            {'Alignment': 5.0, 'Realism': 4.0, 'Aesthetics': 3.0, 'Plausibility': 4.5},
            {'Alignment': 4.5, 'Realism': 5.0, 'Aesthetics': 4.0, 'Plausibility': 3.5}
        ],
        'student_scalar': [4.2, 3.8],
        'human_annotations': [
            {'Alignment': 4.8, 'Realism': 3.9, 'Aesthetics': 3.1, 'Plausibility': 4.4},
            {'Alignment': 4.6, 'Realism': 4.9, 'Aesthetics': 3.9, 'Plausibility': 3.6}
        ],
        'primary_dimension': ['Alignment', 'Realism']
    }
    df = pd.DataFrame(mock_data)
    
    # Save to parquet
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = raw_dir / "z_reward.parquet"
    df.to_parquet(parquet_path)
    
    # Test loading
    loaded_df = load_and_align_data(str(parquet_path))
    
    # Verify data was loaded correctly
    assert len(loaded_df) == 2
    assert 'prompt' in loaded_df.columns
    assert 'teacher_scores' in loaded_df.columns
    assert 'student_scalar' in loaded_df.columns
    assert 'human_annotations' in loaded_df.columns
    assert 'primary_dimension' in loaded_df.columns

def test_load_and_align_data_missing_columns(tmp_path):
    """Test that missing columns are handled gracefully."""
    # Create a mock dataset with missing columns
    mock_data = {
        'prompt': ['test prompt 1'],
        # Missing image_url, teacher_scores, etc.
    }
    df = pd.DataFrame(mock_data)
    
    # Save to parquet
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = raw_dir / "incomplete.parquet"
    df.to_parquet(parquet_path)
    
    # Test loading - should handle missing columns without crashing
    # The function should return a dataframe with the loaded columns
    # and potentially mark missing data
    loaded_df = load_and_align_data(str(parquet_path))
    
    # Verify the dataframe exists and has the loaded column
    assert len(loaded_df) == 1
    assert 'prompt' in loaded_df.columns
