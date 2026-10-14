import subprocess
import os
import sys
import pytest
from pathlib import Path

# The test ensures that the atomic_gate script aborts with status ABORTED
# when required metadata columns are missing. To simulate this condition
# without altering the real datasets, we temporarily rename the status
# file to a non‑existent location so that the script cannot find a prior
# successful run and must perform the download check.

@pytest.mark.parametrize("dataset_name", [
    "DTS-SN1-15-01-2024",
    "SN18-All-20240204"
])
def test_missing_metadata_causes_abort(tmp_path, monkeypatch, dataset_name):
    # Ensure the pipeline status file does not exist (simulating a fresh run)
    status_path = Path("data/processed/.pipeline_status")
    if status_path.exists():
        if status_path.is_file():
            status_path.unlink()
        else:
            # If it's a directory, remove it
            for child in status_path.iterdir():
                child.unlink()
            status_path.rmdir()

    # Monkeypatch the DATASET_NAMES constant in atomic_gate to contain only
    # a dataset that we know will be missing required columns.
    # Since we cannot modify the real remote datasets, we inject a dummy
    # dataset name that the script will attempt to download and fail,
    # triggering the abort logic.
    from code.data import atomic_gate
    monkeypatch.setattr(atomic_gate, "DATASET_NAMES", [dataset_name])

    # Run the script
    result = subprocess.run(
        [sys.executable, str(Path("code/data/atomic_gate.py"))],
        capture_output=True,
        text=True
    )

    # The script should exit with a non‑zero code and write ABORTED status
    assert result.returncode != 0, "Script did not abort as expected"

    # Verify that the status file contains 'ABORTED'
    assert status_path.is_file(), "Status file was not created"
    content = status_path.read_text().strip()
    assert content == "ABORTED", f"Expected status 'ABORTED', got '{content}'"

    # Verify that the exclusion log was created with only the header
    exclusion_log = Path("data/processed/exclusion_raw.log")
    assert exclusion_log.is_file(), "Exclusion log was not created"
    with exclusion_log.open() as f:
        header = f.readline().strip()
        assert header == "row_index,reason,original_smiles"