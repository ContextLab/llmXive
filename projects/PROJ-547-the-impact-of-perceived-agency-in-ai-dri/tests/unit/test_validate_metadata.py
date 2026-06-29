"""
Unit tests for the ``validate_metadata`` script.

The tests create temporary files and a corresponding ``metadata.yaml``
file, then invoke the validation logic. One test checks the happy path
(checksums match) and the other checks that a mismatch triggers a
``SystemExit`` with a non‑zero exit code.
"""

import sys
from pathlib import Path

import pytest
import yaml

from data_acquisition.download_agency_scale import compute_sha256
from data_acquisition import validate_metadata


@pytest.fixture
def setup_dataset(tmp_path, monkeypatch):
    """
    Create a temporary ``datasets`` directory with a single file and a
    matching ``metadata.yaml``. Returns the path to the temporary root.
    """
    datasets_dir = tmp_path / "datasets"
    datasets_dir.mkdir()

    # Create a dummy file
    file_path = datasets_dir / "sample.txt"
    file_path.write_text("sample content for checksum testing")

    # Compute its checksum
    checksum = compute_sha256(file_path)

    # Write metadata.yaml
    metadata = {str(file_path.relative_to(tmp_path)): checksum}
    (datasets_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata))

    # Ensure the script sees the temporary directory as the CWD
    monkeypatch.chdir(tmp_path)

    return tmp_path


def test_validate_metadata_success(setup_dataset):
    """
    Validation should succeed when all checksums match.
    """
    # Import inside the test to ensure the monkeypatched cwd is active
    from data_acquisition.validate_metadata import main

    # The script should exit with status 0 (i.e., not raise SystemExit)
    # because ``main`` calls ``sys.exit(0)`` at the end.
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_validate_metadata_failure(tmp_path, monkeypatch):
    """
    Validation should abort with a non‑zero exit code when a checksum
    does not match.
    """
    datasets_dir = tmp_path / "datasets"
    datasets_dir.mkdir()

    # Create a file whose content will be altered after metadata is written
    file_path = datasets_dir / "corrupt.txt"
    file_path.write_text("original content")
    correct_checksum = compute_sha256(file_path)

    # Write metadata with the *correct* checksum
    metadata = {str(file_path.relative_to(tmp_path)): correct_checksum}
    (datasets_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata))

    # Corrupt the file
    file_path.write_text("tampered content")

    # Change cwd to the temporary root
    monkeypatch.chdir(tmp_path)

    from data_acquisition.validate_metadata import main

    # Expect a SystemExit with code 1 due to checksum mismatch
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1