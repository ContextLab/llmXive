import os
import pytest
from pathlib import Path

# Helper to locate the project root via the `paths` utility
from llmxive_toolkit import paths

def test_data_ingestion_schema():
    """
    Verify that the raw data directory contains at least one subject folder
    with a NIfTI file. This ensures the download step produced real data.
    """
    raw_dir = paths.data("raw", "HCP_1200")
    assert raw_dir.is_dir(), f"Raw data directory missing: {raw_dir}"
    subjects = [p for p in raw_dir.iterdir() if p.is_dir()]
    assert len(subjects) > 0, "No subject directories found in data/raw/"

    # Check that each subject directory contains a NIfTI file
    for subj in subjects:
        nifti_files = list(subj.rglob("*.nii")) + list(subj.rglob("*.nii.gz"))
        assert len(nifti_files) > 0, f"No NIfTI files found for subject {subj.name}"
        break  # One subject is enough for the test

@pytest.mark.skip(reason="Motion exclusion logic tested in later tasks")
def test_motion_exclusion_logic():
    pass

@pytest.mark.skip(reason="Regression summary generation tested in later tasks")
def test_final_json_output_schema():
    pass
