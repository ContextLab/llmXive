"""
Integration tests for the ingestion module (T013).

Tests the complete ingestion pipeline:
- Dataset download and filtering
- CSV saving
- Hash computation and state update
"""
import os
import pytest
import pandas as pd
from pathlib import Path
import yaml
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datasets import Dataset

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import (
    load_and_filter_dataset,
    save_to_csv,
    update_hash_state,
    run_ingestion_pipeline,
    compute_sha256_file,
    OUTPUT_FILENAME,
    OUTPUT_DIR,
    STATE_DIR,
    HASH_FILENAME
)
from error_handling import DatasetDownloadError

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_base = tempfile.mkdtemp()
    temp_raw = os.path.join(temp_base, "data", "raw")
    temp_state = os.path.join(temp_base, "state")
    os.makedirs(temp_raw, exist_ok=True)
    os.makedirs(temp_state, exist_ok=True)
    
    yield {
        "base": temp_base,
        "raw": temp_raw,
        "state": temp_state
    }
    
    # Cleanup
    shutil.rmtree(temp_base)

@pytest.fixture
def mock_dataset():
    """Create a mock dataset for testing."""
    mock_data = [
        {"prompt": "Test prompt 1", "label": "Authority-framed", "id": 1},
        {"prompt": "Test prompt 2", "label": "Exception-poisoning", "id": 2},
        {"prompt": "Test prompt 3", "label": "Other-label", "id": 3},
        {"prompt": "Test prompt 4", "label": "Authority-framed", "id": 4},
    ]
    return Dataset.from_list(mock_data)

def test_load_and_filter_dataset_success(mock_dataset):
    """Test successful dataset loading and filtering."""
    with patch('ingestion.load_dataset') as mock_load:
        # Mock the streaming dataset
        mock_load.return_value = mock_dataset
        
        df = load_and_filter_dataset()
        
        assert len(df) == 3  # Should have 3 items (excluding "Other-label")
        assert 'prompt' in df.columns
        assert 'label' in df.columns
        assert all(df['label'].isin(['Authority-framed', 'Exception-poisoning']))

def test_load_and_filter_dataset_no_matches(mock_dataset):
    """Test when no items match the target labels."""
    mock_data = [
        {"prompt": "Test prompt 1", "label": "Other-label", "id": 1},
        {"prompt": "Test prompt 2", "label": "Another-label", "id": 2},
    ]
    mock_empty = Dataset.from_list(mock_data)
    
    with patch('ingestion.load_dataset') as mock_load:
        mock_load.return_value = mock_empty
        
        with pytest.raises(DatasetDownloadError) as exc_info:
            load_and_filter_dataset()
        
        assert "No items found" in str(exc_info.value)

def test_save_to_csv(temp_dirs):
    """Test saving DataFrame to CSV."""
    df = pd.DataFrame({
        'prompt': ['Test 1', 'Test 2'],
        'label': ['Authority-framed', 'Exception-poisoning']
    })
    
    output_path = Path(temp_dirs['raw']) / "test_output.csv"
    save_to_csv(df, output_path)
    
    assert output_path.exists()
    
    # Verify content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 2
    assert list(saved_df.columns) == ['prompt', 'label']

def test_update_hash_state(temp_dirs):
    """Test hash computation and state update."""
    # Create a test file
    test_file = Path(temp_dirs['raw']) / "test.txt"
    test_file.write_text("Test content")
    
    state_file = Path(temp_dirs['state']) / HASH_FILENAME
    
    update_hash_state(test_file, state_file)
    
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert 'medmis_subset' in state or 'test.txt' in str(state)
    assert 'sha256' in str(state)

def test_compute_sha256_file(temp_dirs):
    """Test SHA-256 computation."""
    test_file = Path(temp_dirs['raw']) / "test.txt"
    test_file.write_text("Test content")
    
    hash1 = compute_sha256_file(test_file)
    hash2 = compute_sha256_file(test_file)
    
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2  # Same content should produce same hash

def test_run_ingestion_pipeline_failure():
    """Test pipeline failure handling."""
    with patch('ingestion.load_dataset') as mock_load:
        mock_load.side_effect = Exception("Network error")
        
        with pytest.raises(DatasetDownloadError):
            run_ingestion_pipeline()

def test_integration_full_pipeline(temp_dirs, mock_dataset):
    """Test the full ingestion pipeline with mocked data."""
    # Patch the directories
    with patch('ingestion.OUTPUT_DIR', temp_dirs['raw']), \
         patch('ingestion.STATE_DIR', temp_dirs['state']), \
         patch('ingestion.load_dataset') as mock_load:
        
        mock_load.return_value = mock_dataset
        
        output_path = run_ingestion_pipeline()
        
        assert output_path.exists()
        assert output_path.name == OUTPUT_FILENAME
        
        # Verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) == 3  # Filtered items
        
        # Verify state file
        state_path = Path(temp_dirs['state']) / HASH_FILENAME
        assert state_path.exists()
        
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        assert 'medmis_subset' in state
        assert 'sha256' in state['medmis_subset']
