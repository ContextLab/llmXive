import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.correlation_io import save_correlation_results
from src.config import load_config

@pytest.fixture
def sample_correlation_results():
    """Create a sample correlation results DataFrame."""
    return pd.DataFrame({
        'r': [0.45, -0.32, 0.12, 0.55],
        'p': [0.001, 0.023, 0.156, 0.0001],
        'q': [0.005, 0.045, 0.234, 0.0003],
        'is_moderate': [True, True, False, True],
        'is_meaningful': [True, True, False, True],
        'status': ['success', 'success', 'success', 'success']
    })

@pytest.fixture
def blocked_correlation_results():
    """Create a blocked status DataFrame."""
    return pd.DataFrame({
        'r': [np.nan],
        'p': [np.nan],
        'q': [np.nan],
        'is_moderate': [False],
        'is_meaningful': [False],
        'status': ['blocked']
    })

def test_save_correlation_results_creates_file(sample_correlation_results, tmp_path):
    """Test that save_correlation_results creates the output file."""
    output_path = tmp_path / "test_results.csv"
    
    result_path = save_correlation_results(
        sample_correlation_results, 
        output_path=str(output_path),
        force=True
    )
    
    assert result_path.exists()
    assert result_path == output_path
    
    # Verify content
    saved_df = pd.read_csv(result_path)
    assert len(saved_df) == 4
    assert list(saved_df.columns) == ['r', 'p', 'q', 'is_moderate', 'is_meaningful', 'status']

def test_save_correlation_results_empty_dataframe(blocked_correlation_results, tmp_path):
    """Test that save_correlation_results handles blocked status with empty data."""
    output_path = tmp_path / "blocked_results.csv"
    
    # Should not raise for blocked status
    result_path = save_correlation_results(
        blocked_correlation_results,
        output_path=str(output_path),
        force=True
    )
    
    assert result_path.exists()
    saved_df = pd.read_csv(result_path)
    assert saved_df['status'].iloc[0] == 'blocked'

def test_save_correlation_results_creates_directory(tmp_path):
    """Test that save_correlation_results creates parent directories if needed."""
    nested_path = tmp_path / "subdir1" / "subdir2" / "results.csv"
    
    sample_df = pd.DataFrame({
        'r': [0.5],
        'p': [0.01],
        'q': [0.02],
        'is_moderate': [True],
        'is_meaningful': [True],
        'status': ['success']
    })
    
    result_path = save_correlation_results(
        sample_df,
        output_path=str(nested_path),
        force=True
    )
    
    assert result_path.exists()
    assert result_path.parent.exists()

def test_save_correlation_results_data_integrity(sample_correlation_results, tmp_path):
    """Test that saved data matches input data exactly."""
    output_path = tmp_path / "integrity_test.csv"
    
    save_correlation_results(
        sample_correlation_results,
        output_path=str(output_path),
        force=True
    )
    
    saved_df = pd.read_csv(output_path)
    
    # Check all values match
    pd.testing.assert_frame_equal(
        sample_correlation_results.reset_index(drop=True),
        saved_df.reset_index(drop=True)
    )

def test_save_correlation_results_missing_columns(tmp_path):
    """Test that save_correlation_results raises ValueError for missing columns."""
    incomplete_df = pd.DataFrame({
        'r': [0.5],
        'p': [0.01],
        # Missing q, is_moderate, is_meaningful, status
    })
    
    output_path = tmp_path / "incomplete.csv"
    
    with pytest.raises(ValueError) as exc_info:
        save_correlation_results(incomplete_df, output_path=str(output_path), force=True)
    
    assert "Missing required columns" in str(exc_info.value)

def test_save_correlation_results_file_exists_error(sample_correlation_results, tmp_path):
    """Test that save_correlation_results raises FileExistsError if file exists and force=False."""
    output_path = tmp_path / "exists.csv"
    
    # Create the file first
    save_correlation_results(
        sample_correlation_results,
        output_path=str(output_path),
        force=True
    )
    
    # Try to save again without force
    with pytest.raises(FileExistsError):
        save_correlation_results(
            sample_correlation_results,
            output_path=str(output_path),
            force=False
        )

def test_save_correlation_results_empty_non_blocked(tmp_path):
    """Test that save_correlation_results raises FileNotFoundError for empty non-blocked data."""
    empty_df = pd.DataFrame(columns=['r', 'p', 'q', 'is_moderate', 'is_meaningful', 'status'])
    output_path = tmp_path / "empty.csv"
    
    with pytest.raises(FileNotFoundError) as exc_info:
        save_correlation_results(empty_df, output_path=str(output_path), force=True)
    
    assert "empty and status is not 'blocked'" in str(exc_info.value)
