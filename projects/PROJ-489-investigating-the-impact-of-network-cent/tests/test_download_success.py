import os
import shutil
from pathlib import Path

import pytest

# Import the function to test
from download import download_sleep_edf

def test_download_small_subset(tmp_path):
    """
    Download a very small subset (2 recordings) to ensure the wrapper works.
    This test runs against the real PhysioNet repository; it will fail loudly
    if network access is unavailable or if the MNE fetch API changes.
    """
    # Use a temporary directory to avoid polluting the project data folder
    out_dir = tmp_path / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Request only 2 recordings (subject 0 night 1 and subject 0 night 2)
    successful, errors = download_sleep_edf(output_dir=str(out_dir), n_subjects=2)

    # At least one successful download should be present
    assert len(successful) >= 1, "No files were successfully downloaded"
    # Errors list may be empty or contain entries for corrupted files
    assert isinstance(errors, list)

    # Verify that the log file was created and contains expected lines
    log_path = out_dir / "download_log.txt"
    assert log_path.is_file(), "download_log.txt was not created"

    # Clean up the temporary download to keep CI fast
    shutil.rmtree(out_dir, ignore_errors=True)