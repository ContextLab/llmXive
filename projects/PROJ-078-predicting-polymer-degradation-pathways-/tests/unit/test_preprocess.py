import pytest
import pandas as pd
import os
import json
import tempfile
from pathlib import Path

# Import the functions we want to test
# Note: We assume these are defined in code/preprocess.py
# Since we cannot import directly in this test file without the full environment,
# we will mock the logic or test the main entry point if possible.
# However, for unit tests, we should test the core logic.
# Let's assume we can import the functions if we set up the path correctly.
# For now, we will write tests that would pass if the functions were implemented correctly.

# Mock the get_project_paths to use a temporary directory
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import (
    compute_checksum,
    check_augmentation_trigger,
    load_processed_polyester_dataset,
    subsample_dataset_stratified,
    save_dataset
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_dataframe():
    data = {
        'smiles': ['CCO', 'CC(=O)O', 'C1=CC=CC=C1', 'CC(=O)OC', 'CCO'],
        'degradation_pathway': ['hydrolysis', 'hydrolysis', 'oxidation', 'hydrolysis', 'thermal'],
        'temperature': [25, 30, 40, 25, 50],
        'pH': [7, 7, 7, 8, 7]
    }
    return pd.DataFrame(data)

def test_compute_checksum(temp_dir):
    """Test that compute_checksum returns a valid SHA-256 hash."""
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_checksum(str(test_file))
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_check_augmentation_trigger_missing(temp_dir):
    """Test that check_augmentation_trigger returns None if file is missing."""
    trigger_path = Path(temp_dir) / "nonexistent.json"
    result = check_augmentation_trigger(str(trigger_path))
    assert result is None

def test_check_augmentation_trigger_valid(temp_dir):
    """Test that check_augmentation_trigger returns the correct dict."""
    trigger_path = Path(temp_dir) / "trigger.json"
    trigger_data = {"action": "none", "n": 200}
    with open(trigger_path, 'w') as f:
        json.dump(trigger_data, f)
    
    result = check_augmentation_trigger(str(trigger_path))
    assert result == trigger_data

def test_load_processed_polyester_dataset_missing(temp_dir):
    """Test that load_processed_polyester_dataset raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_processed_polyester_dataset(str(Path(temp_dir) / "missing.csv"))

def test_load_processed_polyester_dataset_valid(temp_dir, sample_dataframe):
    """Test that load_processed_polyester_dataset loads a CSV correctly."""
    csv_path = Path(temp_dir) / "data.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    
    df = load_processed_polyester_dataset(str(csv_path))
    assert len(df) == len(sample_dataframe)
    assert list(df.columns) == list(sample_dataframe.columns)

def test_subsample_dataset_stratified(temp_dir, sample_dataframe):
    """Test that subsample_dataset_stratified performs stratified sampling."""
    output_path = Path(temp_dir) / "output.csv"
    
    # Create a larger dataset for testing
    large_df = pd.concat([sample_dataframe] * 10, ignore_index=True)
    
    result_path = subsample_dataset_stratified(large_df, str(output_path), seed=42)
    
    assert os.path.exists(result_path)
    result_df = pd.read_csv(result_path)
    
    # Check that the result is a subset
    assert len(result_df) <= len(large_df)
    
    # Check that the distribution of degradation_pathway is preserved (approximately)
    original_dist = large_df['degradation_pathway'].value_counts(normalize=True)
    result_dist = result_df['degradation_pathway'].value_counts(normalize=True)
    
    # Allow for some tolerance in the distribution
    for pathway in original_dist.index:
        if pathway in result_dist.index:
            assert abs(original_dist[pathway] - result_dist[pathway]) < 0.1

def test_subsample_dataset_stratified_no_pathway_column(temp_dir):
    """Test subsampling when no degradation pathway column exists."""
    df = pd.DataFrame({
        'smiles': ['CCO', 'CC(=O)O'],
        'temperature': [25, 30]
    })
    output_path = Path(temp_dir) / "output_no_pathway.csv"
    
    # This should fall back to random sampling
    result_path = subsample_dataset_stratified(df, str(output_path), seed=42)
    
    assert os.path.exists(result_path)
    result_df = pd.read_csv(result_path)
    assert len(result_df) == len(df)  # Should keep all if n <= 500

def test_save_dataset(temp_dir, sample_dataframe):
    """Test that save_dataset saves the file and returns the checksum."""
    output_path = Path(temp_dir) / "saved.csv"
    checksum = save_dataset(sample_dataframe, str(output_path), "Test Save")
    
    assert os.path.exists(output_path)
    assert len(checksum) == 64
