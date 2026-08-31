import pytest
import json
import pandas as pd
from pathlib import Path
import tempfile
import os

from download import (
    compute_sha256, 
    filter_dataset_columns, 
    write_exclusion_log,
    write_blocked_status
)
from config import get_data_dir, get_processed_dir

def test_compute_sha256():
    """Test SHA256 checksum computation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n1,2\n3,4")
        temp_path = Path(f.name)
    
    checksum = compute_sha256(temp_path)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)
    
    os.unlink(temp_path)

def test_filter_dataset_columns():
    """Test column filtering logic."""
    df = pd.DataFrame({
        'duration_estimate': [1, 2, 3],
        'stimulus_sequence': ['a', 'b', 'c'],
        'participant_id': [1, 1, 2],
        'extra_col': [4, 5, 6]
    })
    
    required = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    assert filter_dataset_columns(df, required) is True
    
    # Missing column
    df_missing = df.drop(columns=['duration_estimate'])
    assert filter_dataset_columns(df_missing, required) is False

def test_write_exclusion_log():
    """Test exclusion log writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusion_log.json"
        exclusions = [
            {'dataset_id': 'test:123', 'status': 'excluded', 'reason': 'missing columns'}
        ]
        
        write_exclusion_log(exclusions, log_path)
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['dataset_id'] == 'test:123'
        assert data[0]['status'] == 'excluded'

def test_write_blocked_status():
    """Test blocked status writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = Path(tmpdir) / "blocked_status.json"
        
        write_blocked_status("No valid datasets", status_path)
        
        assert status_path.exists()
        with open(status_path, 'r') as f:
            data = json.load(f)
        
        assert data['status'] == 'blocked'
        assert data['reason'] == 'No valid datasets'
        assert 'timestamp' in data