import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# We need to mock the get_path and ensure_dirs from config/utils if running in isolation
# but for the unit test of the logic, we can test the functions directly if we pass dataframes.
# However, the functions rely on file I/O. We will test the core logic functions.

from code.derivation import finalize_dataset, generate_derivation_log

def test_finalize_dataset_deduplication():
    """Test that duplicate participant IDs are removed."""
    data = {
        'participant_id': ['P1', 'P1', 'P2', 'P3'],
        'label': ['Control', 'AD', 'MCI', 'Control'],
        'text': ['word word', 'word word', 'word word', 'word word']
    }
    df = pd.DataFrame(data)
    
    result = finalize_dataset(df)
    
    assert len(result) == 3
    assert result['participant_id'].nunique() == 3
    assert 'P1' in result['participant_id'].values
    
    # Check sorting
    assert result['participant_id'].is_monotonic_increasing or result['participant_id'].is_monotonic_decreasing
    # Actually, sort_values ensures it's sorted.
    assert list(result['participant_id']) == ['P1', 'P2', 'P3']

def test_finalize_dataset_type_casting():
    """Test that columns are cast to string."""
    data = {
        'participant_id': [123, 456],
        'label': ['Control', 1],
        'text': ['hello', 'world']
    }
    df = pd.DataFrame(data)
    
    result = finalize_dataset(df)
    
    assert result['participant_id'].dtype == 'object' # pandas string representation
    assert result['label'].dtype == 'object'

def test_generate_derivation_log_creates_file():
    """Test that the derivation log is written correctly."""
    data = {
        'participant_id': ['P1'],
        'label': ['Control'],
        'text': ['test text']
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        log_path = Path(tmpdir) / "derivation_log.json"
        
        # Mock the output path for the log function to use the tmpdir
        # The function generates a log path based on output_path
        # We need to call the function with a valid output_path
        
        # Since the function writes to disk, we check if the file exists
        log_data = generate_derivation_log(df, output_path)
        
        assert os.path.exists(log_path)
        
        with open(log_path, 'r') as f:
            saved_log = json.load(f)
        
        assert saved_log['record_counts']['input'] == 1
        assert saved_log['record_counts']['output'] == 1
        assert 'T016' in str(saved_log['steps_applied'])
        assert saved_log['data_quality_checks']['null_labels'] == 0
