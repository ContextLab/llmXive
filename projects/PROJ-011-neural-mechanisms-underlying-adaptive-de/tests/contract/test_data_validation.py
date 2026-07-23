"""
Contract Test for Data Validation.
Verifies OpenNeuro ds003694 structure and required behavioral columns.
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from preprocessing.data_validation import validate_dataset_structure, validate_participant_data
from utils.io import save_csv, save_json

@pytest.fixture
def temp_dataset_root(tmp_path):
    """
    Creates a temporary directory structure mimicking OpenNeuro ds003694.
    """
    root = tmp_path / "ds003694"
    root.mkdir()
    
    # Create dataset_description.json
    desc = {
        "Name": "Test Dataset",
        "DatasetType": "raw",
        "BIDSVersion": "1.6.0"
    }
    save_json(str(root / "dataset_description.json"), desc)
    
    # Create a participant
    sub_id = "sub-01"
    ses_id = "ses-01"
    sub_dir = root / sub_id / ses_id
    sub_dir.mkdir(parents=True)
    
    # Create func directory and dummy NIfTI (just a file for existence check)
    func_dir = sub_dir / "func"
    func_dir.mkdir()
    nifti_file = func_dir / f"{sub_id}_{ses_id}_task-social_bold.nii.gz"
    nifti_file.touch() # Create empty file to simulate existence
    
    # Create beh directory
    beh_dir = sub_dir / "beh"
    beh_dir.mkdir()
    
    # Create valid behavioral TSV
    beh_file = beh_dir / f"{sub_id}_{ses_id}_task-social_beh.tsv"
    data = {
        "private_belief": [0, 1, 1, 0],
        "social_feedback": [1, 0, 1, 1],
        "choice": [1, 0, 0, 1],
        "timestamp": [0.0, 1.0, 2.0, 3.0]
    }
    save_csv(str(beh_file), pd.DataFrame(data), sep="\t")
    
    return str(root), sub_id, ses_id

@pytest.fixture
def temp_invalid_dataset_root(tmp_path):
    """
    Creates a temporary directory structure with missing behavioral columns.
    """
    root = tmp_path / "ds003694_invalid"
    root.mkdir()
    
    # Create dataset_description.json
    desc = {"Name": "Invalid Test", "BIDSVersion": "1.6.0"}
    save_json(str(root / "dataset_description.json"), desc)
    
    sub_id = "sub-02"
    ses_id = "ses-01"
    sub_dir = root / sub_id / ses_id
    sub_dir.mkdir(parents=True)
    
    func_dir = sub_dir / "func"
    func_dir.mkdir()
    (func_dir / f"{sub_id}_{ses_id}_task-social_bold.nii.gz").touch()
    
    beh_dir = sub_dir / "beh"
    beh_dir.mkdir()
    
    # Create behavioral TSV with MISSING required columns
    beh_file = beh_dir / f"{sub_id}_{ses_id}_task-social_beh.tsv"
    data = {
        "trial_type": ["A", "B"],
        "response_time": [100, 200]
        # Missing private_belief, social_feedback, choice
    }
    save_csv(str(beh_file), pd.DataFrame(data), sep="\t")
    
    return str(root), sub_id, ses_id

def test_validate_dataset_structure_valid(temp_dataset_root):
    """Test that valid dataset structure passes validation."""
    root, _, _ = temp_dataset_root
    is_valid, errors = validate_dataset_structure(root)
    
    assert is_valid, f"Valid dataset failed: {errors}"
    assert len(errors) == 0

def test_validate_dataset_structure_missing_description(tmp_path):
    """Test that missing dataset_description.json fails validation."""
    root = tmp_path / "empty_ds"
    root.mkdir()
    # No dataset_description.json created
    
    is_valid, errors = validate_dataset_structure(str(root))
    
    assert not is_valid
    assert any("dataset_description.json" in err for err in errors)

def test_validate_participant_data_valid(temp_dataset_root):
    """Test that participant with valid data passes."""
    root, sub_id, ses_id = temp_dataset_root
    is_valid, errors = validate_participant_data(root, sub_id, ses_id)
    
    assert is_valid, f"Valid participant failed: {errors}"
    assert len(errors) == 0

def test_validate_participant_data_missing_nifti(tmp_path):
    """Test that participant missing NIfTI fails."""
    root = tmp_path / "ds"
    root.mkdir()
    (root / "dataset_description.json").write_text("{}")
    
    sub_id = "sub-03"
    ses_id = "ses-01"
    sub_dir = root / sub_id / ses_id
    sub_dir.mkdir(parents=True)
    # No func dir created
    
    is_valid, errors = validate_participant_data(str(root), sub_id, ses_id)
    
    assert not is_valid
    assert any("functional image" in err for err in errors)

def test_validate_participant_data_missing_behavioral_columns(temp_invalid_dataset_root):
    """
    Contract test: Verifies that behavioral logs MUST contain
    'private_belief', 'social_feedback', and 'choice'.
    """
    root, sub_id, ses_id = temp_invalid_dataset_root
    is_valid, errors = validate_participant_data(root, sub_id, ses_id)
    
    assert not is_valid, "Participant with missing columns should fail validation."
    
    # Verify specific error message about columns
    col_errors = [e for e in errors if "missing required columns" in e]
    assert len(col_errors) == 1, f"Expected exactly one column error, got: {errors}"
    
    error_msg = col_errors[0]
    assert "private_belief" in error_msg
    assert "social_feedback" in error_msg
    assert "choice" in error_msg

def test_validate_participant_data_missing_behavioral_file(tmp_path):
    """Test that participant missing behavioral file fails."""
    root = tmp_path / "ds"
    root.mkdir()
    (root / "dataset_description.json").write_text("{}")
    
    sub_id = "sub-04"
    ses_id = "ses-01"
    sub_dir = root / sub_id / ses_id
    sub_dir.mkdir(parents=True)
    
    (sub_dir / "func").mkdir()
    (sub_dir / "func" / f"{sub_id}_{ses_id}_task-social_bold.nii.gz").touch()
    # No beh dir created
    
    is_valid, errors = validate_participant_data(str(root), sub_id, ses_id)
    
    assert not is_valid
    assert any("Missing behavioral log" in err for err in errors)
