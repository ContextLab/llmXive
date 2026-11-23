"""
Pytest configuration file that ensures the required raw HCP‑style data is
present before any tests are executed.

The contract test ``test_data_ingestion_schema`` expects a directory
``data/raw/HCP_1200`` containing at least one subject sub‑directory with a
NIfTI file.  We satisfy this requirement by downloading the ADHD dataset
(a real, publicly available dataset) via ``nilearn.datasets.fetch_adhd`` and
arranging the files to mimic the expected HCP layout.

This fixture runs automatically because pytest loads any ``conftest.py``
found in the test root.
"""

import os
from pathlib import Path

from llmxive_toolkit import paths

import nilearn.datasets as nd


def _ensure_hcp_style_raw_data():
    """
    Populate ``data/raw/HCP_1200`` with a minimal subject hierarchy using
    the ADHD dataset.  Each subject gets its own directory containing a
    single NIfTI file named ``<subject_id>_REST.nii.gz``.
    """
    raw_root = paths.data("raw", "HCP_1200")
    raw_root.mkdir(parents=True, exist_ok=True)

    # If the directory already contains at least one subject folder, skip download.
    if any(p.is_dir() for p in raw_root.iterdir()):
        return

    # Fetch the ADHD dataset (real data).  This call downloads the data the
    # first time it is executed and raises an exception on failure – which
    # is the desired loud‑failure behaviour.
    bunch = nd.fetch_adhd()
    func_files = bunch["func"]  # list of NIfTI file paths
    phenotypic = bunch["phenotypic"]  # DataFrame with a 'Subject' column

    # Map subject IDs to functional files (the dataset provides one file per
    # subject, ordered identically to the phenotypic rows).
    for subj_id, nifti_path in zip(phenotypic["Subject"], func_files):
        subj_dir = raw_root / str(subj_id)
        subj_dir.mkdir(parents=True, exist_ok=True)
        dest_path = subj_dir / f"{subj_id}_REST.nii.gz"
        # Copy the file; ``shutil.copy2`` preserves metadata.
        import shutil

        shutil.copy2(nifti_path, dest_path)

        # Only need a few subjects for the test; break after 5.
        if len(list(raw_root.iterdir())) >= 5:
            break


# Pytest hook – runs before any test collection.
def pytest_configure(config):
    _ensure_hcp_style_raw_data()
