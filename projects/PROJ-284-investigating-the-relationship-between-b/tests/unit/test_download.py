"""
Contract test for the download module – ensures that the ADHD dataset can be fetched.
"""

import pytest
from code.data.download import fetch_adhd_dataset, save_phenotypic_csv, create_subject_list

def test_fetch_returns_nifti_on_success(monkeypatch):
    # The real fetch uses nilearn which is available in the test environment.
    df = fetch_adhd_dataset()
    assert not df.empty
    # Verify required columns exist
    for col in ["Subject", "MeanFD"]:
        assert col in df.columns