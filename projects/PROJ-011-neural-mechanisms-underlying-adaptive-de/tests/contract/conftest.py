"""
Pytest configuration for contract tests.

This file provides fixtures and configuration specific to contract testing,
ensuring isolation and proper setup for data validation tests.
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys

# Ensure the project root is in the path for imports
# This is crucial when running tests from the tests/ directory
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture
def temp_dataset_dir():
    """
    Create a temporary directory structure mimicking a valid OpenNeuro dataset.
    Used for testing validation logic without needing real data.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create root files
        (tmp_path / "dataset_description.json").write_text('{"Name": "TestDS003694", "DatasetType": "raw"}')
        (tmp_path / "participants.tsv").write_text("participant_id\tage\tsex\nsub-01\t25\tM\nsub-02\t30\tF")
        (tmp_path / "participants.json").write_text("{}")
        
        # Create subject directories
        for i in range(1, 3): # Create sub-01 and sub-02 for testing
            subj = f"sub-{i:02d}"
            subj_dir = tmp_path / subj
            subj_dir.mkdir()
            
            # Create func directory
            func_dir = subj_dir / "func"
            func_dir.mkdir()
            
            # Create mock NIfTI files (empty files for testing structure)
            for task in ["social_feedback", "private_belief"]:
                nifti_file = func_dir / f"{subj}_task-{task}_bold.nii.gz"
                json_file = func_dir / f"{subj}_task-{task}_bold.json"
                
                nifti_file.touch()
                json_file.write_text("{}")
            
            # Create anat directory
            anat_dir = subj_dir / "anat"
            anat_dir.mkdir()
            t1w_file = anat_dir / f"{subj}_T1w.nii.gz"
            t1w_file.touch()
            
        yield tmp_path

@pytest.fixture
def invalid_dataset_dir(temp_dataset_dir):
    """
    Create a temporary directory with intentional structural errors.
    Used to test error detection logic.
    """
    # Remove a required file to simulate missing data
    (temp_dataset_dir / "participants.tsv").unlink()
    
    # Remove a subject directory
    (temp_dataset_dir / "sub-02").rmdir()
    
    yield temp_dataset_dir
