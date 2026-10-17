import subprocess
import sys
from pathlib import Path

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(300)
def test_download_two_subjects():
    """Ensure that downloading two subjects succeeds and creates expected artifacts."""
    # Run the download script
    result = subprocess.run(
        [sys.executable, "code/download.py", "--subjects", "2"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Download script failed: {result.stderr}"

    # Check that the raw data directory exists and contains at least one subject folder
    raw_dir = paths.data("raw")
    assert raw_dir.is_dir(), "Raw data directory was not created"

    # There should be at least one sub‑directory matching the BIDS subject pattern
    subject_dirs = [p for p in raw_dir.iterdir() if p.is_dir() and p.name.startswith("sub-")]
    assert len(subject_dirs) >= 1, "No subject directories found after download"

    # Checksums file must exist
    checksums_path = raw_dir / "checksums.json"
    assert checksums_path.is_file(), "checksums.json not written"

    # Verify that condition verification passes (i.e., the script would have exited otherwise)
    # Re‑run the condition gate explicitly
    cond_result = subprocess.run(
        [sys.executable, "code/verify_references.py", "--stage", "conditions"],
        capture_output=True,
        text=True,
    )
    assert cond_result.returncode == 0, f"Condition verification failed: {cond_result.stderr}"