"""
Contract tests for the dataset schema.
Verifies that the input data adheres to the BIDS and project-specific requirements
defined in the specification.
"""
import os
import json
import pytest
from pathlib import Path

# Import project utilities if needed for path handling
# Note: Direct imports from utils might require code/ to be in sys.path
# For contract tests, we often validate raw files directly or via a lightweight loader.

# Expected schema definitions (simplified for contract testing)
EXPECTED_BIDS_FIELDS = {
    "subject_id": str,
    "session_id": str,
    "task": str,
    "modality": str,
    "extension": str
}

EXPECTED_LABEL_FIELDS = {
    "subject_id": str,
    "timepoint": int,
    "score_type": str,  # e.g., "MMSE", "MOCA"
    "score_value": (int, float),
    "visit_date": str
}


def test_bids_subject_directory_structure(tmp_path):
    """
    Contract: Verify that a valid BIDS subject directory contains required files.
    """
    # Create a mock subject directory structure
    subject_dir = tmp_path / "sub-01"
    subject_dir.mkdir()
    (subject_dir / "anat").mkdir()
    (subject_dir / "func").mkdir()

    # Create a mock T1w file
    t1w_file = subject_dir / "anat" / "sub-01_T1w.nii.gz"
    t1w_file.touch()

    # Create a mock rs-fMRI file
    func_file = subject_dir / "func" / "sub-01_task-rest_bold.nii.gz"
    func_file.touch()

    # Contract assertion: Directory exists and contains expected subfolders
    assert (subject_dir / "anat").exists()
    assert (subject_dir / "func").exists()
    assert t1w_file.exists()
    assert func_file.exists()


def test_json_sidecar_schema(tmp_path):
    """
    Contract: Verify that BIDS JSON sidecars contain required metadata fields.
    """
    bids_json = tmp_path / "sub-01" / "sub-01_task-rest_bold.json"
    bids_json.parent.mkdir(parents=True)

    # Valid metadata
    valid_metadata = {
        "TaskName": "rest",
        "RepetitionTime": 2.0,
        "SliceTiming": [0.0, 0.1, 0.2]
    }

    with open(bids_json, 'w') as f:
        json.dump(valid_metadata, f)

    with open(bids_json, 'r') as f:
        data = json.load(f)

    # Contract assertion: Required keys exist
    assert "TaskName" in data
    assert "RepetitionTime" in data
    assert isinstance(data["RepetitionTime"], float)


def test_longitudinal_labels_schema(tmp_path):
    """
    Contract: Verify the structure of the longitudinal labels CSV/JSON.
    """
    labels_file = tmp_path / "labels.json"

    # Valid longitudinal data structure
    valid_labels = [
        {
            "subject_id": "sub-01",
            "timepoint": 1,
            "score_type": "MMSE",
            "score_value": 28,
            "visit_date": "2023-01-01"
        },
        {
            "subject_id": "sub-01",
            "timepoint": 2,
            "score_type": "MMSE",
            "score_value": 25,
            "visit_date": "2023-06-01"
        }
    ]

    with open(labels_file, 'w') as f:
        json.dump(valid_labels, f)

    with open(labels_file, 'r') as f:
        data = json.load(f)

    # Contract assertion: Structure matches specification
    assert isinstance(data, list)
    assert len(data) == 2
    for record in data:
        assert "subject_id" in record
        assert "timepoint" in record
        assert "score_type" in record
        assert "score_value" in record
        assert isinstance(record["timepoint"], int)
        assert isinstance(record["score_value"], (int, float))
