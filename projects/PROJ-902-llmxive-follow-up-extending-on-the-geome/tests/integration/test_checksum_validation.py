"""Integration test for checksum validation.

This test ensures that the checksum validation logic in the
``src.data.checksums`` module raises an exception when a file's
recorded SHA‑256 checksum does not match the actual content.
"""

import pytest
from pathlib import Path

# Import the validation function from the project code.
from src.data.checksums import validate_checksums

# The download script populates ``data/gsm8k`` and writes the
# ``checksums.txt`` file.  The test assumes that the dataset has
# already been downloaded by a previous step (e.g. task T009).
# If the directory does not exist, the test will fail early,
# signalling that the prerequisite download step has not been run.
DATA_DIR = Path("data/gsm8k")
CHECKSUM_FILE = DATA_DIR / "checksums.txt"

def _find_a_data_file():
    """Return the first regular file in ``DATA_DIR`` that is not the
    checksum manifest.  Raises ``FileNotFoundError`` if no such file is
    present.
    """
    for p in DATA_DIR.iterdir():
        if p.is_file() and p.name != CHECKSUM_FILE.name:
            return p
    raise FileNotFoundError("No data file found to corrupt for checksum test.")

def test_checksum_validation_raises_on_corrupted_file():
    """Corrupt a file and verify that ``validate_checksums`` raises."""
    # Preconditions – the dataset directory and checksum manifest must exist.
    assert DATA_DIR.is_dir(), f"Dataset directory {DATA_DIR!s} does not exist."
    assert CHECKSUM_FILE.is_file(), f"Checksum file {CHECKSUM_FILE!s} is missing."

    # Pick a file to corrupt.
    target_file = _find_a_data_file()

    # Record the original size so we can restore the file after the test.
    original_size = target_file.stat().st_size

    # Corrupt the file by appending a single byte.
    with open(target_file, "ab") as f:
        f.write(b"\x00")

    # The validation should now detect a mismatch and raise.
    with pytest.raises(Exception):
        validate_checksums(DATA_DIR)

    # Clean‑up: truncate the file back to its original size to avoid
    # contaminating subsequent tests.
    with open(target_file, "ab") as f:
        f.truncate(original_size)