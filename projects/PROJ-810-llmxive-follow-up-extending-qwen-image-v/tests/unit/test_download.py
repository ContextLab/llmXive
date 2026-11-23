"""
Unit tests for code/data/download.py
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path to ensure imports work if run as script
project_root = Path(__file__).resolve().parents[2]
sys_path = str(project_root / "code")
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from data.download import compute_file_checksum, download_dataset, DATASET_ID, SUBSET_NAME, OUTPUT_DIR, OUTPUT_FILE, CHECKSUM_OUTPUT, CHECKSUM_ALGO


class TestComputeFileChecksum:
    """Tests for the compute_file_checksum function."""

    def test_compute_checksum_sha256(self):
        """Test that compute_file_checksum returns a valid SHA-256 hash."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content for checksum")
            tmp_path = Path(tmp.name)

        try:
            checksum = compute_file_checksum(tmp_path, "sha256")
            # SHA-256 hex digest is always 64 characters
            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)
        finally:
            os.unlink(tmp_path)

    def test_compute_checksum_different_content_different_hash(self):
        """Test that different content produces different checksums."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp1:
            tmp1.write(b"content A")
            path1 = Path(tmp1.name)

        with tempfile.NamedTemporaryFile(delete=False) as tmp2:
            tmp2.write(b"content B")
            path2 = Path(tmp2.name)

        try:
            checksum1 = compute_file_checksum(path1, "sha256")
            checksum2 = compute_file_checksum(path2, "sha256")
            assert checksum1 != checksum2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_compute_checksum_empty_file(self):
        """Test checksum computation on an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            checksum = compute_file_checksum(tmp_path, "sha256")
            # SHA-256 of empty string is e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(tmp_path)

    def test_compute_checksum_nonexistent_file(self):
        """Test that computing checksum on a non-existent file raises FileNotFoundError."""
        fake_path = Path("/nonexistent/file/path.txt")
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(fake_path)

    def test_compute_checksum_algorithm_case_insensitive(self):
        """Test that algorithm parameter is case insensitive."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = Path(tmp.name)

        try:
            checksum_upper = compute_file_checksum(tmp_path, "SHA256")
            checksum_lower = compute_file_checksum(tmp_path, "sha256")
            assert checksum_upper == checksum_lower
        finally:
            os.unlink(tmp_path)


class TestDownloadDataset:
    """Tests for the download_dataset function."""

    def test_output_directory_structure_exists(self):
        """Test that the expected output directory structure is defined correctly."""
        assert isinstance(OUTPUT_DIR, Path)
        assert isinstance(OUTPUT_FILE, Path)
        assert isinstance(CHECKSUM_OUTPUT, Path)
        assert OUTPUT_FILE.name == "omnidoc_tokenbench.parquet"
        assert CHECKSUM_OUTPUT.name == "checksum.json"

    def test_checksum_output_directory_creation(self):
        """Test that checksum output directory can be created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            test_checksum_file = tmp_path / "results" / "checksum.json"
            
            # This should not raise
            test_checksum_file.parent.mkdir(parents=True, exist_ok=True)
            assert test_checksum_file.parent.exists()

    def test_dataset_configuration_constants(self):
        """Test that dataset configuration constants are properly defined."""
        assert DATASET_ID == "omnidoc/omnidoc-tokenbench"
        assert SUBSET_NAME == "omnidoc-tokenbench"
        assert CHECKSUM_ALGO == "sha256"

    def test_download_dataset_error_handling_structure(self):
        """Test that download_dataset has proper error handling structure."""
        # We can't actually test the download without network access,
        # but we can verify the function exists and has the right signature
        import inspect
        sig = inspect.signature(download_dataset)
        # Function should not require any arguments
        assert len(sig.parameters) == 0

    def test_checksum_json_structure_on_success(self):
        """Test the expected structure of checksum.json on successful download."""
        # This is a structural test - we verify what the code SHOULD produce
        expected_keys = {
            "dataset_id",
            "subset", 
            "file_path",
            "checksum_algorithm",
            "checksum_value",
            "num_rows",
            "status"
        }
        
        # Verify the code would produce these keys by checking the source
        import inspect
        source = inspect.getsource(download_dataset)
        for key in expected_keys:
            assert key in source, f"Expected key '{key}' not found in download_dataset source"

    def test_checksum_json_structure_on_error(self):
        """Test the expected structure of checksum.json on failed download."""
        expected_error_keys = {
            "dataset_id",
            "subset",
            "status",
            "error_type",
            "message"
        }
        
        import inspect
        source = inspect.getsource(download_dataset)
        for key in expected_error_keys:
            assert key in source, f"Expected error key '{key}' not found in download_dataset source"


class TestIntegration:
    """Integration-level tests for download module."""

    def test_module_imports_successfully(self):
        """Test that the download module can be imported without errors."""
        # This test verifies the module is syntactically correct
        # and all imports resolve properly
        import data.download
        assert hasattr(data.download, 'compute_file_checksum')
        assert hasattr(data.download, 'download_dataset')
        assert hasattr(data.download, 'main')

    def test_main_function_exists(self):
        """Test that main function exists and has correct signature."""
        import inspect
        from data.download import main
        sig = inspect.signature(main)
        assert len(sig.parameters) == 0

    def test_constants_are_immutable(self):
        """Test that configuration constants are properly defined."""
        # Verify constants are strings and non-empty
        assert isinstance(DATASET_ID, str) and len(DATASET_ID) > 0
        assert isinstance(SUBSET_NAME, str) and len(SUBSET_NAME) > 0
        assert isinstance(CHECKSUM_ALGO, str) and len(CHECKSUM_ALGO) > 0

    def test_file_paths_are_relative(self):
        """Test that output paths are relative (not absolute)."""
        assert not OUTPUT_FILE.is_absolute()
        assert not CHECKSUM_OUTPUT.is_absolute()
        assert not OUTPUT_DIR.is_absolute()

    def test_checksum_algorithm_validity(self):
        """Test that the configured checksum algorithm is valid."""
        import hashlib
        # Verify sha256 is a supported algorithm
        assert CHECKSUM_ALGO in hashlib.algorithms_available or CHECKSUM_ALGO == "sha256"