"""
Contract Test for Data Validation

Verifies OpenNeuro ds003694 structure requirements.
"""
import os
import sys
from pathlib import Path
import tempfile
import json
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.data_validation import validate_dataset_structure, validate_participant_data
from utils.io import save_json

@pytest.fixture
def mock_openneuro_dataset(tmp_path):
    """
    Create a mock OpenNeuro ds003694 structure for testing.
    
    Expected structure:
    ds003694/
      dataset_description.json
      sub-01/
        func/
          sub-01_task-feedback_bold.nii.gz
          sub-01_task-feedback_events.tsv
        anat/
          sub-01_T1w.nii.gz
      sub-02/
        func/
          sub-02_task-feedback_bold.nii.gz
          sub-02_task-feedback_events.tsv
        anat/
          sub-02_T1w.nii.gz
    """
    base_dir = tmp_path / "ds003694"
    base_dir.mkdir()
    
    # dataset_description.json
    desc = {
        "Name": "Test Dataset",
        "BIDSVersion": "1.6.0"
    }
    save_json(desc, base_dir / "dataset_description.json")
    
    # Create participants
    for sub_id in ["01", "02"]:
        sub_dir = base_dir / f"sub-{sub_id}"
        func_dir = sub_dir / "func"
        anat_dir = sub_dir / "anat"
        
        func_dir.mkdir(parents=True)
        anat_dir.mkdir(parents=True)
        
        # Create dummy files (empty is fine for structure validation)
        (func_dir / f"sub-{sub_id}_task-feedback_bold.nii.gz").touch()
        (func_dir / f"sub-{sub_id}_task-feedback_events.tsv").touch()
        (anat_dir / f"sub-{sub_id}_T1w.nii.gz").touch()
        
    return str(base_dir)

def test_validate_dataset_structure(mock_openneuro_dataset):
    """
    Contract test: Verify that a valid OpenNeuro structure passes validation.
    """
    is_valid, errors = validate_dataset_structure(mock_openneuro_dataset)
    
    assert is_valid, f"Valid dataset structure failed validation: {errors}"
    assert len(errors) == 0

def test_validate_dataset_structure_missing_description(tmp_path):
    """
    Contract test: Verify that missing dataset_description.json fails.
    """
    base_dir = tmp_path / "invalid_ds"
    base_dir.mkdir()
    
    # No dataset_description.json
    is_valid, errors = validate_dataset_structure(str(base_dir))
    
    assert not is_valid
    assert any("dataset_description.json" in str(e) for e in errors)

def test_validate_participant_data_valid(mock_openneuro_dataset):
    """
    Contract test: Verify valid participant data.
    """
    base_dir = Path(mock_openneuro_dataset)
    participant_id = "01"
    
    is_valid, errors = validate_participant_data(base_dir, participant_id)
    
    assert is_valid, f"Valid participant failed validation: {errors}"

def test_validate_participant_data_missing_bold(tmp_path):
    """
    Contract test: Verify missing bold file fails.
    """
    base_dir = tmp_path / "ds003694"
    base_dir.mkdir()
    
    # Create minimal valid structure but missing bold
    sub_dir = base_dir / "sub-01"
    func_dir = sub_dir / "func"
    func_dir.mkdir(parents=True)
    
    # Only events, no bold
    (func_dir / "sub-01_task-feedback_events.tsv").touch()
    
    # dataset_description.json
    save_json({"Name": "Test", "BIDSVersion": "1.6.0"}, base_dir / "dataset_description.json")
    
    is_valid, errors = validate_participant_data(base_dir, "01")
    
    assert not is_valid
    assert any("bold" in str(e).lower() for e in errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
