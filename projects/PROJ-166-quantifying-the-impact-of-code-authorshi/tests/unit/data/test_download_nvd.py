import hashlib
import json
import gzip
import os
import tempfile
from pathlib import Path
import pytest

from data.download_nvd import calculate_sha256, generate_checksum

def test_nvd_checksum_verification():
    """
    Test that the SHA256 checksum calculation matches the expected value.
    We create a temporary file with known content, calculate its checksum,
    and verify it matches the expected hash.
    """
    # Create a temporary file with known content
    test_content = b"Test content for checksum verification"
    expected_hash = hashlib.sha256(test_content).hexdigest()

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp_file:
        tmp_file.write(test_content)
        tmp_path = tmp_file.name

    try:
        # Calculate the SHA256 of the temporary file
        calculated_hash = calculate_sha256(tmp_path)

        # Assert the calculated hash matches the expected hash
        assert calculated_hash == expected_hash, f"Checksum mismatch: {calculated_hash} != {expected_hash}"
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
