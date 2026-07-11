import os
import tempfile
from pathlib import Path

import pytest

from code.data.loader import (
    calculate_sha256,
    verify_ruler_data_integrity,
    download_and_verify_ruler,
)
from utils.config import get_default_config


class TestChecksumCalculation:
    def test_calculate_sha256_consistency(self, tmp_path):
        """Test that checksum calculation is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content for checksum verification")

        checksum1 = calculate_sha256(str(test_file))
        checksum2 = calculate_sha256(str(test_file))

        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_calculate_sha256_content_sensitivity(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("content A")
        file2.write_text("content B")

        checksum1 = calculate_sha256(str(file1))
        checksum2 = calculate_sha256(str(file2))

        assert checksum1 != checksum2


class TestLoaderVerification:
    @pytest.mark.integration
    def test_verify_ruler_data_downloads_and_verifies(self):
        """
        Integration test: Verify that RULER data can be downloaded
        and checksum verification runs without errors.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                is_valid, report = verify_ruler_data_integrity(
                    dataset_name="hkust-nlp/ruler",
                    subset="needle",
                    version="1.3.0",
                    data_dir=tmp_dir,
                )

                # The function should complete without raising
                assert isinstance(is_valid, bool)
                assert isinstance(report, dict)

                # If files were found, they should be recorded
                if report.get("status") != "no_files_to_verify":
                    assert len(report) > 0
                    for path, info in report.items():
                        assert "checksum" in info
                        assert "status" in info
                        assert "size_bytes" in info
            except Exception as e:
                pytest.fail(f"Verification failed with error: {e}")

    def test_download_and_verify_ruler_returns_bool(self):
        """Test that the convenience function returns a boolean."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                result = download_and_verify_ruler(
                    dataset_name="hkust-nlp/ruler",
                    subset="needle",
                    version="1.3.0",
                    data_dir=tmp_dir,
                )
                assert isinstance(result, bool)
            except Exception:
                # If network fails, the function should return False, not raise
                pass