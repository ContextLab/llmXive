import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Mock the dependencies if necessary, but we are testing the logic
# We will create a temporary directory structure that mimics the BIDS dataset
# to test the report generation.

def create_mock_bids_dataset(tmp_path):
    """Create a minimal BIDS dataset structure for testing."""
    # Root
    dataset_desc = {
        "Name": "TestDataset",
        "BIDSVersion": "1.6.0"
    }
    with open(tmp_path / "dataset_description.json", 'w') as f:
        json.dump(dataset_desc, f)
    
    # Participants
    participants_df = pd.DataFrame({
        "participant_id": ["sub-01", "sub-02"],
        "stai": [30, 45]
    })
    participants_df.to_csv(tmp_path / "participants.tsv", sep='\t', index=False)
    
    # Sub-01 func
    func_dir = tmp_path / "sub-01" / "func"
    func_dir.mkdir(parents=True)
    
    # Events file with required columns
    events_df = pd.DataFrame({
        "onset": [0, 1, 2],
        "duration": [0.1, 0.1, 0.1],
        "trial_type": ["stim", "stim", "stim"],
        "x": [100, 105, 110],
        "y": [200, 205, 210],
        "timestamp": [0.0, 0.1, 0.2],
        "valence": [1, -1, 1],
        "recall": [1, 0, 1]
    })
    events_df.to_csv(func_dir / "sub-01_task-rsvp_events.tsv", sep='\t', index=False)
    
    # Task JSON sidecar
    task_json = {
        "RepetitionTime": 2.0,
        "TaskName": "RSVP"
    }
    with open(func_dir / "sub-01_task-rsvp_events.json", 'w') as f:
        json.dump(task_json, f)
        
    return tmp_path

def test_report_generation_success(tmp_path):
    """Test that a successful verification report is generated."""
    data_dir = create_mock_bids_dataset(tmp_path)
    output_file = tmp_path / "report.json"
    
    # Import the function
    from generate_verification_report import generate_report
    
    report = generate_report(str(data_dir), str(output_file))
    
    assert output_file.exists()
    assert report["success"] is True
    assert report["variable_presence"]["x"] is True
    assert report["variable_presence"]["y"] is True
    assert report["variable_presence"]["timestamp"] is True
    assert report["variable_presence"]["valence"] is True
    assert report["variable_presence"]["recall"] is True
    assert report["variable_presence"]["stai"] is True
    assert report["geometry_status"]["status"] in ["calibrated", "defaults_applied"]
    
    # Verify file content
    with open(output_file, 'r') as f:
        loaded_report = json.load(f)
    assert loaded_report["success"] is True

def test_report_generation_missing_variables(tmp_path):
    """Test report generation when variables are missing."""
    # Create a dataset missing 'stai'
    data_dir = tmp_path / "missing_stai"
    data_dir.mkdir()
    
    # Participants without STAI
    participants_df = pd.DataFrame({
        "participant_id": ["sub-01"]
    })
    participants_df.to_csv(data_dir / "participants.tsv", sep='\t', index=False)
    
    # Events with x, y, timestamp, valence, recall
    func_dir = data_dir / "sub-01" / "func"
    func_dir.mkdir(parents=True)
    events_df = pd.DataFrame({
        "onset": [0],
        "duration": [0.1],
        "x": [100],
        "y": [200],
        "timestamp": [0.0],
        "valence": [1],
        "recall": [1]
    })
    events_df.to_csv(func_dir / "sub-01_task-rsvp_events.tsv", sep='\t', index=False)
    
    from generate_verification_report import generate_report
    
    output_file = tmp_path / "report_missing.json"
    report = generate_report(str(data_dir), str(output_file))
    
    # Should fail because STAI is missing
    assert report["success"] is False
    assert report["variable_presence"]["stai"] is False
    assert report["variable_presence"]["x"] is True
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    assert loaded["success"] is False

def test_report_geometry_defaults(tmp_path):
    """Test that defaults are applied when geometry metadata is missing."""
    data_dir = create_mock_bids_dataset(tmp_path)
    # Remove any existing geometry metadata if we had added it (we didn't in mock)
    # The mock doesn't have specific geometry sidecars, so it should use defaults.
    
    from generate_verification_report import generate_report
    
    output_file = tmp_path / "report_defaults.json"
    report = generate_report(str(data_dir), str(output_file))
    
    assert report["geometry_status"]["defaults_used"] is True
    assert report["geometry_status"]["ivt_threshold"] is not None
    assert report["geometry_status"]["screen_width"] == 1920
    assert report["geometry_status"]["sampling_rate"] == 60