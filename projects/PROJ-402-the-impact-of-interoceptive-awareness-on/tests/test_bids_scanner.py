"""
Tests for the BIDS Scanner utilities (T012).

Tests the logic to scan BIDS events.tsv files for 'Schandry' or 'heartbeat' tasks.
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from code.utils.bids_scanner import (
    find_events_files,
    scan_events_for_tasks,
    scan_bids_dataset_for_interoception,
    TARGET_TASKS
)

@pytest.fixture
def temp_bids_dataset():
    """Create a temporary BIDS-like structure with events.tsv files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create subdirectories
        sub1_dir = root / "sub-01" / "func"
        sub1_dir.mkdir(parents=True)
        sub2_dir = root / "sub-02" / "func"
        sub2_dir.mkdir(parents=True)
        sub3_dir = root / "sub-03" / "func"
        sub3_dir.mkdir(parents=True)

        # File 1: Contains 'Schandry' task
        df1 = pd.DataFrame({
            'onset': [0, 10, 20],
            'duration': [1, 1, 1],
            'task': ['Schandry', 'Schandry', 'Schandry'],
            'stim_type': ['auditory', 'auditory', 'auditory']
        })
        (sub1_dir / "sub-01_task-schandry_events.tsv").write_text(df1.to_csv(sep='\t', index=False))

        # File 2: Contains 'heartbeat' task (mixed case)
        df2 = pd.DataFrame({
            'onset': [0, 5],
            'duration': [2, 2],
            'task': ['HeartBeat', 'HEARTBEAT'],
            'response': [1, 0]
        })
        (sub2_dir / "sub-02_task-heartbeat_events.tsv").write_text(df2.to_csv(sep='\t', index=False))

        # File 3: Contains unrelated task
        df3 = pd.DataFrame({
            'onset': [0],
            'duration': [1],
            'task': ['rest'],
            'stim_type': ['none']
        })
        (sub3_dir / "sub-03_task-rest_events.tsv").write_text(df3.to_csv(sep='\t', index=False))

        yield root

def test_find_events_files(temp_bids_dataset):
    """Test that all events.tsv files are found recursively."""
    files = find_events_files(temp_bids_dataset)
    assert len(files) == 3
    for f in files:
        assert f.name == "events.tsv"
        assert f.exists()

def test_scan_events_for_tasks_schandry(temp_bids_dataset):
    """Test scanning a file with 'Schandry' task."""
    events_file = temp_bids_dataset / "sub-01" / "func" / "sub-01_task-schandry_events.tsv"
    result = scan_events_for_tasks(events_file)
    
    assert result is not None
    assert result['error'] is None
    assert 'schandry' in result['found_tasks']
    assert len(result['found_tasks']) == 1

def test_scan_events_for_tasks_heartbeat_case_insensitive(temp_bids_dataset):
    """Test scanning a file with 'HeartBeat' (mixed case) task."""
    events_file = temp_bids_dataset / "sub-02" / "func" / "sub-02_task-heartbeat_events.tsv"
    result = scan_events_for_tasks(events_file)
    
    assert result is not None
    assert result['error'] is None
    assert 'heartbeat' in result['found_tasks']
    assert len(result['found_tasks']) == 1

def test_scan_events_for_tasks_unrelated(temp_bids_dataset):
    """Test scanning a file with unrelated task."""
    events_file = temp_bids_dataset / "sub-03" / "func" / "sub-03_task-rest_events.tsv"
    result = scan_events_for_tasks(events_file)
    
    assert result is not None
    # Should have an error or empty found_tasks indicating no target found
    assert len(result['found_tasks']) == 0
    assert result['error'] is not None

def test_scan_bids_dataset_for_interoception(temp_bids_dataset):
    """Test the full dataset scan logic."""
    summary = scan_bids_dataset_for_interoception(temp_bids_dataset)
    
    assert summary['total_files_scanned'] == 3
    assert len(summary['files_with_target_tasks']) == 2
    assert 'schandry' in summary['unique_tasks_found']
    assert 'heartbeat' in summary['unique_tasks_found']
    assert len(summary['missing_tasks']) == 0

def test_scan_bids_dataset_missing_tasks(temp_bids_dataset):
    """Test dataset scan when only one target task is present."""
    # Create a new temp dir with only Schandry
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        sub_dir = root / "sub-01" / "func"
        sub_dir.mkdir(parents=True)
        
        df = pd.DataFrame({
            'onset': [0],
            'duration': [1],
            'task': ['Schandry']
        })
        (sub_dir / "sub-01_task-schandry_events.tsv").write_text(df.to_csv(sep='\t', index=False))
        
        summary = scan_bids_dataset_for_interoception(root)
        
        assert 'schandry' in summary['unique_tasks_found']
        assert 'heartbeat' in summary['missing_tasks']
        assert len(summary['missing_tasks']) == 1