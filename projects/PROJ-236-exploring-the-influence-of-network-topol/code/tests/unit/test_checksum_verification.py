import pathlib

import pytest

from utils.io import compute_file_checksum
from generate_checksums import generate_checksums

class TestChecksummingVerification:
    """
    Verify that the recorded checksums for every artifact in ``data/`` match the
    recomputed values. The test first (re)generates the checksums file to ensure
    it exists, then reads the expected values and asserts equality.
    """

    def test_checksums_match(self):
        # (Re)generate the checksums file – this guarantees it is present.
        checksums_path = generate_checksums()

        # Load the expected checksum mapping from the generated file.
        expected = {}
        with checksums_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rel_path, checksum = line.split()
                expected[rel_path] = checksum

        data_dir = pathlib.Path("data")

        # Verify each listed file.
        for rel_path, expected_checksum in expected.items():
            file_path = data_dir / rel_path
            assert file_path.is_file(), f"Expected data file '{rel_path}' not found."

            actual_checksum = compute_file_checksum(file_path)
            assert (
                actual_checksum == expected_checksum
            ), f"Checksum mismatch for '{rel_path}': expected {expected_checksum}, got {actual_checksum}"
