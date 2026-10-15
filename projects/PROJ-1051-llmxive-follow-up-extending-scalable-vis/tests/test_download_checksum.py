"""
Unit test for the download checksum generation.
Ensures that the checksum file is created after a successful download.
"""

import pathlib

def test_checksum_file_exists():
    checksum_path = pathlib.Path("artifacts/checksums/downloads.yaml")
    assert checksum_path.is_file(), "Checksum file was not created"
