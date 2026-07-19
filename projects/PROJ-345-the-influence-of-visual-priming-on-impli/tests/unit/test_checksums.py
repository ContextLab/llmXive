import os
import csv
import tempfile
import yaml
from pathlib import Path
import pytest

# Import the functions to test
from state.checksums import (
    calculate_file_checksum,
    calculate_linked_metadata_percentage,
    verify_and_record_checksums,
    load_state_yaml,
    save_state_yaml,
    DEFAULT_LINKED_THRESHOLD
)

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    return tmp_path / "state"

@pytest.fixture
def temp_raw_dir(tmp_path):
    """Create a temporary directory with dummy raw files."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "file1.txt").write_text("content1")
    (raw_dir / "subdir").mkdir()
    (raw_dir / "subdir" / "file2.txt").write_text("content2")
    return raw_dir

@pytest.fixture
def temp_linked_trials(tmp_path):
    """Create a temporary linked_trials.csv file."""
    trials_file = tmp_path / "linked_trials.csv"
    with open(trials_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['trial_id', 'response_time', 'stimulus_id', 'prime_condition', 'participant_id'])
        writer.writeheader()
        # 8 linked, 2 unlinked -> 80%
        writer.writerow({'trial_id': '1', 'response_time': '500', 'stimulus_id': 'img_001', 'prime_condition': 'positive', 'participant_id': 'P1'})
        writer.writerow({'trial_id': '2', 'response_time': '600', 'stimulus_id': 'img_002', 'prime_condition': 'positive', 'participant_id': 'P1'})
        writer.writerow({'trial_id': '3', 'response_time': '450', 'stimulus_id': 'img_003', 'prime_condition': 'negative', 'participant_id': 'P1'})
        writer.writerow({'trial_id': '4', 'response_time': '550', 'stimulus_id': 'img_004', 'prime_condition': 'negative', 'participant_id': 'P1'})
        writer.writerow({'trial_id': '5', 'response_time': '520', 'stimulus_id': 'img_005', 'prime_condition': 'neutral', 'participant_id': 'P2'})
        writer.writerow({'trial_id': '6', 'response_time': '480', 'stimulus_id': 'img_006', 'prime_condition': 'neutral', 'participant_id': 'P2'})
        writer.writerow({'trial_id': '7', 'response_time': '510', 'stimulus_id': 'img_007', 'prime_condition': 'positive', 'participant_id': 'P2'})
        writer.writerow({'trial_id': '8', 'response_time': '530', 'stimulus_id': 'img_008', 'prime_condition': 'positive', 'participant_id': 'P2'})
        # Unlinked
        writer.writerow({'trial_id': '9', 'response_time': '600', 'stimulus_id': '', 'prime_condition': 'positive', 'participant_id': 'P3'})
        writer.writerow({'trial_id': '10', 'response_time': '610', 'stimulus_id': None, 'prime_condition': 'negative', 'participant_id': 'P3'})
    return trials_file

def test_calculate_file_checksum(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    
    checksum = calculate_file_checksum(file_path)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length
    # Known checksum for "hello world"
    assert checksum == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

def test_calculate_linked_metadata_percentage(temp_linked_trials):
    # 8 out of 10 are linked -> 0.8
    pct = calculate_linked_metadata_percentage(temp_linked_trials)
    assert pct == 0.8
    assert pct < 1.0

def test_calculate_linked_metadata_percentage_empty_file(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("trial_id,response_time,stimulus_id\n") # Header only
    pct = calculate_linked_metadata_percentage(file_path)
    assert pct == 0.0

def test_calculate_linked_metadata_percentage_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.csv"
    pct = calculate_linked_metadata_percentage(missing_path)
    assert pct == 0.0

def test_verify_and_record_checksums(temp_state_dir, temp_raw_dir):
    state_yaml = temp_state_dir / "state.yaml"
    
    state = verify_and_record_checksums(state_yaml, temp_raw_dir)
    
    assert 'raw_data_checksums' in state
    assert 'file1.txt' in state['raw_data_checksums']
    assert 'subdir/file2.txt' in state['raw_data_checksums']
    
    # Verify file was written
    assert state_yaml.exists()
    with open(state_yaml, 'r') as f:
        loaded = yaml.safe_load(f)
    assert loaded == state

def test_load_save_state_yaml(temp_state_dir):
    state_file = temp_state_dir / "test.yaml"
    data = {"key": "value", "nested": {"a": 1}}
    
    save_state_yaml(state_file, data)
    loaded = load_state_yaml(state_file)
    
    assert loaded == data

def test_default_threshold():
    assert DEFAULT_LINKED_THRESHOLD == 0.95