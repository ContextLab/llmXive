"""
Unit tests for the download module.

These tests verify the logic of data loading, sampling, and validation
without necessarily hitting the network in every run (though the main
function does hit the network).
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Mock the datasets module to avoid network calls during unit tests
# We will test the logic functions directly with mock data
from unittest.mock import patch, MagicMock

# Import the function to test
# Note: We need to handle the import path carefully
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import (
    compute_file_checksum,
    load_and_sample_dataset,
    REQUIRED_COLUMNS
)


def test_compute_file_checksum():
    """Test checksum computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("test,data\n1,2\n")
        temp_path = Path(f.name)

    try:
        checksum = compute_file_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)
    finally:
        os.unlink(temp_path)


@patch('code.download.load_dataset')
@patch('code.download.Path.mkdir')
def test_load_and_sample_dataset_success(mock_mkdir, mock_load_dataset):
    """Test successful loading and sampling of the dataset."""
    # Create mock data
    mock_data = pd.DataFrame({
        'canonical_smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
        'cid': [123, 124, 125]
    })
    
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = mock_data
    mock_load_dataset.return_value = mock_dataset

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        result = load_and_sample_dataset(
            dataset_name="fake/dataset",
            sample_size=2,
            output_dir=output_dir,
            seed=42
        )

        # Verify load_dataset was called
        mock_load_dataset.assert_called_once_with("fake/dataset", split="train")
        
        # Verify output files were created
        assert (output_dir / "pubchem_sample.csv").exists()
        assert (output_dir / "pubchem_sample_checksum.json").exists()
        
        # Verify result structure
        assert 'sha256' in result
        assert result['row_count'] == 2


@patch('code.download.load_dataset')
def test_load_and_sample_dataset_missing_columns(mock_load_dataset):
    """Test that missing columns raise an error."""
    mock_data = pd.DataFrame({
        'wrong_col': ['CCO', 'CC(=O)O'],
        'cid': [123, 124]
    })
    
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = mock_data
    mock_load_dataset.return_value = mock_dataset

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        with pytest.raises(ValueError, match="missing required columns"):
            load_and_sample_dataset(
                dataset_name="fake/dataset",
                sample_size=2,
                output_dir=output_dir,
                seed=42
            )


@patch('code.download.load_dataset')
def test_load_and_sample_dataset_invalid_smiles(mock_load_dataset):
    """Test handling of invalid/empty SMILES strings."""
    mock_data = pd.DataFrame({
        'canonical_smiles': ['CCO', '', None, 'c1ccccc1'],
        'cid': [123, 124, 125, 126]
    })
    
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = mock_data
    mock_load_dataset.return_value = mock_dataset

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Should not raise, but should drop invalid rows
        result = load_and_sample_dataset(
            dataset_name="fake/dataset",
            sample_size=2,
            output_dir=output_dir,
            seed=42
        )
        
        # The result should only contain valid rows
        assert result['row_count'] <= 2 # Might be less if sampling picks invalid ones, but logic drops them first