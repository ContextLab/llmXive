"""
Unit tests for the `filter_subjects` function in `code/data/loader.py`.

Scenarios covered:
1. Missing fMRI scan → exclusion reason "MISSING_SCAN".
2. Missing creativity (CAQ) score → exclusion reason "MISSING_SCORE".
3. Excessive motion → exclusion reason "HIGH_MOTION".
4. Fully valid subject → included in the output CSV.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test and the Participant dataclass
from data.loader import filter_subjects, Participant

# Helper to locate the shared exclusion log file
EXCLUSION_LOG_PATH = Path("data/interim/data_exclusion_log.txt")
INCLUDED_CSV_PATH = Path("data/interim/included_subjects.csv")

@pytest.fixture(autouse=True)
def clean_output_files():
    """
    Ensure a clean environment before each test run:
    - Remove any existing exclusion log.
    - Remove any existing included subjects CSV.
    - Remove any temporary fMRI files created during the test.
    """
    # Cleanup before test
    if EXCLUSION_LOG_PATH.is_file():
        EXCLUSION_LOG_PATH.unlink()
    if INCLUDED_CSV_PATH.is_file():
        INCLUDED_CSV_PATH.unlink()

    # Ensure data/raw directory exists
    raw_root = Path("data/raw")
    raw_root.mkdir(parents=True, exist_ok=True)

    yield  # Run the test

    # Cleanup after test
    if EXCLUSION_LOG_PATH.is_file():
        EXCLUSION_LOG_PATH.unlink()
    if INCLUDED_CSV_PATH.is_file():
        INCLUDED_CSV_PATH.unlink()
    # Remove any temporary subject directories under data/raw
    for subject_dir in raw_root.glob("hcp_*"):
        if subject_dir.is_dir():
            for child in subject_dir.iterdir():
                child.unlink()
            subject_dir.rmdir()

def _create_fmri_file(subject_id: str):
    """
    Helper that creates an empty (but existent) fMRI file for a given subject
    in the location expected by `filter_subjects`.
    """
    fmri_path = Path("data", "raw", f"hcp_{subject_id}",
                     f"sub-{subject_id}_task-rest_bold.dtseries.nii")
    fmri_path.parent.mkdir(parents=True, exist_ok=True)
    # Write a tiny placeholder (real content not needed for existence check)
    fmri_path.write_bytes(b"placeholder")
    return fmri_path

def test_filter_subjects_exclusion_and_inclusion():
    """
    Verify that `filter_subjects` correctly logs exclusions and writes the
    included subjects CSV.
    """
    # ------------------------------------------------------------------
    # 1. Define the manifest (list of subject IDs)
    # ------------------------------------------------------------------
    manifest = ["001", "002", "003", "004"]

    # ------------------------------------------------------------------
    # 2. Create fMRI files for subjects 002, 003, 004 (subject 001 will be missing)
    # ------------------------------------------------------------------
    fmri_002 = _create_fmri_file("002")
    fmri_003 = _create_fmri_file("003")
    fmri_004 = _create_fmri_file("004")
    # Note: subject 001 intentionally has no file to trigger MISSING_SCAN

    # ------------------------------------------------------------------
    # 3. Build the behavioral dictionary
    # ------------------------------------------------------------------
    behavioral = {
        # Subject 001: missing scan → behavioral content irrelevant
        "001": {
            "age": 25,
            "sex": "M",
            "education": 16,
            "CAQ": 3.0,
            "motion_fd": 0.2,
            "motion_vol_proportion": 0.1,
        },
        # Subject 002: missing CAQ score
        "002": {
            "age": 28,
            "sex": "F",
            "education": 18,
            # "CAQ" omitted on purpose
            "motion_fd": 0.3,
            "motion_vol_proportion": 0.05,
        },
        # Subject 003: high motion
        "003": {
            "age": 30,
            "sex": "M",
            "education": 14,
            "CAQ": 4.2,
            "motion_fd": 0.7,               # exceeds fd threshold (0.5)
            "motion_vol_proportion": 0.05,
        },
        # Subject 004: fully valid
        "004": {
            "age": 27,
            "sex": "F",
            "education": 16,
            "CAQ": 3.5,
            "motion_fd": 0.3,
            "motion_vol_proportion": 0.1,
        },
    }

    # ------------------------------------------------------------------
    # 4. Run the filtering function
    # ------------------------------------------------------------------
    included = filter_subjects(manifest, behavioral)

    # ------------------------------------------------------------------
    # 5. Assertions on returned Participant objects
    # ------------------------------------------------------------------
    assert isinstance(included, list)
    assert len(included) == 1
    participant = included[0]
    assert isinstance(participant, Participant)
    assert participant.subject_id == "004"
    assert participant.age == 27
    assert participant.sex == "F"
    assert participant.education == 16
    assert participant.creativity_score == 3.5
    assert participant.fmri_path == fmri_004
    assert participant.motion_fd == 0.3

    # ------------------------------------------------------------------
    # 6. Verify exclusion log contents
    # ------------------------------------------------------------------
    assert EXCLUSION_LOG_PATH.is_file(), "Exclusion log file was not created"
    log_df = pd.read_csv(EXCLUSION_LOG_PATH)

    # Expect three exclusion entries (one per problematic subject)
    assert len(log_df) == 3, f"Expected 3 exclusion rows, got {len(log_df)}"

    # Check that each subject appears with the correct reason
    reasons_by_subject = dict(zip(log_df["subject_id"], log_df["reason"]))
    assert reasons_by_subject["001"] == "MISSING_SCAN"
    assert reasons_by_subject["002"] == "MISSING_SCORE"
    assert reasons_by_subject["003"] == "HIGH_MOTION"

    # ------------------------------------------------------------------
    # 7. Verify the included subjects CSV
    # ------------------------------------------------------------------
    assert INCLUDED_CSV_PATH.is_file(), "Included subjects CSV was not created"
    included_df = pd.read_csv(INCLUDED_CSV_PATH)

    # Should contain exactly one row for subject 004
    assert len(included_df) == 1
    row = included_df.iloc[0]
    assert row["subject_id"] == "004"
    assert row["age"] == 27
    assert row["sex"] == "F"
    assert row["education"] == 16
    assert row["creativity_score"] == 3.5
    # The path stored in the CSV should match the absolute (or relative) path
    # produced by `filter_subjects`.  We compare the string representation.
    assert row["rest_fmri_path"] == str(fmri_004)

# The module contains only the test; PyTest will discover and run it.