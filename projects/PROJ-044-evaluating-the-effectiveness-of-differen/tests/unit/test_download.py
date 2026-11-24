"""
Unit tests for the FEMNIST download module.

The tests verify that:
1. The downloader creates the expected parquet files and checksum.
2. Requesting the excluded 'shakespeare' dataset raises the exact ValueError.
3. Requesting an unknown dataset raises a generic Unsupported‑dataset error.
"""

import pytest
import tempfile
from pathlib import Path

from code.data.download import download_femnist, download_dataset, DataFetchError, EXCLUSION_MESSAGE


class TestFEMNISTDownload:
    def test_download_creates_files(self):
        """Download FEMNIST and check that train/test parquet files and checksum exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            # Perform the download (real network call – will be executed in CI)
            train_path, test_path = download_femnist(out_dir)

            # Verify files exist
            assert train_path.is_file(), f"{train_path} not found"
            assert test_path.is_file(), f"{test_path} not found"

            # Verify checksum file exists and matches concatenated hash
            checksum_path = out_dir / "femnist.sha256"
            assert checksum_path.is_file(), "Checksum file missing"

            # Compute expected hash
            combined = train_path.read_bytes() + test_path.read_bytes()
            import hashlib

            expected_hash = hashlib.sha256(combined).hexdigest()
            recorded_hash = checksum_path.read_text().split()[0]
            assert recorded_hash == expected_hash, "Checksum mismatch"

    def test_shakespeare_exclusion(self):
        """Requesting the excluded dataset must raise the exact ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            with pytest.raises(ValueError, match=EXCLUSION_MESSAGE):
                download_dataset("shakespeare", out_dir)

    def test_unknown_dataset(self):
        """Requesting an unsupported dataset must raise a generic ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            with pytest.raises(ValueError, match="Unsupported dataset"):
                download_dataset("unknown_dataset", out_dir)
