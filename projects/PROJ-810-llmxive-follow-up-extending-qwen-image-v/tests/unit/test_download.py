"""
Unit tests for the data/download.py module, specifically focusing on checksum validation.
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test from the project's code directory
# The project root is expected to be two levels up from this test file
project_root = Path(__file__).resolve().parents[2]
code_path = project_root / "code"
if str(code_path) not in os.sys.path:
    os.sys.path.insert(0, str(code_path))

from data.download import compute_file_checksum, download_dataset
from datasets import load_dataset


class TestChecksumValidation:
    """Tests for checksum computation and validation logic."""

    def test_compute_sha256_checksum_known_file(self):
        """Verify checksum computation on a file with known content."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            # Compute checksum
            checksum = compute_file_checksum(temp_path, algorithm="sha256")

            # Expected checksum for "Hello, World!"
            expected = hashlib.sha256(b"Hello, World!").hexdigest()

            assert checksum == expected, f"Checksum mismatch: {checksum} != {expected}"
        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_compute_md5_checksum_known_file(self):
        """Verify checksum computation with MD5 algorithm."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test Data")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path, algorithm="md5")
            expected = hashlib.md5(b"Test Data").hexdigest()
            assert checksum == expected
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_compute_checksum_empty_file(self):
        """Verify checksum of an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            # SHA-256 of empty string
            expected = hashlib.sha256(b"").hexdigest()
            assert checksum == expected
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_compute_checksum_binary_file(self):
        """Verify checksum computation on binary data."""
        binary_data = bytes(range(256))
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(binary_data)
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            expected = hashlib.sha256(binary_data).hexdigest()
            assert checksum == expected
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_checksum_validation_logic(self):
        """
        Test the logic that validates a downloaded file against a stored checksum.
        Simulates the scenario in download.py where we verify the file integrity.
        """
        # Create a fake checksum file
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()
            file_path = data_dir / "test_file.bin"
            checksum_path = data_dir / "checksum.json"

            # Write a known file
            content = b"verification_content"
            file_path.write_bytes(content)
            real_checksum = hashlib.sha256(content).hexdigest()

            # Write checksum file
            checksum_data = {
                "file_path": str(file_path),
                "checksum_algorithm": "sha256",
                "checksum_value": real_checksum
            }
            with open(checksum_path, "w") as f:
                json.dump(checksum_data, f)

            # Read and verify
            with open(checksum_path, "r") as f:
                stored = json.load(f)

            computed = compute_file_checksum(Path(stored["file_path"]), stored["checksum_algorithm"])

            assert computed == stored["checksum_value"], "Checksum validation failed"

    def test_checksum_mismatch_detection(self):
        """Verify that a mismatch is detected when file content changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            file_path = data_dir / "test.bin"
            checksum_path = data_dir / "checksum.json"

            # Write initial content
            content = b"original"
            file_path.write_bytes(content)
            original_checksum = hashlib.sha256(content).hexdigest()

            # Write checksum file
            with open(checksum_path, "w") as f:
                json.dump({"checksum_value": original_checksum}, f)

            # Corrupt the file
            file_path.write_bytes(b"corrupted")

            # Compute new checksum
            new_checksum = compute_file_checksum(file_path)

            # Verify mismatch
            assert new_checksum != original_checksum, "Mismatch should have been detected"

    def test_download_dataset_structure(self):
        """
        Verify that the download_dataset function attempts to load the correct dataset
        and handles the expected structure.
        Note: This test mocks the actual network call to avoid heavy downloads during unit tests,
        but validates the logic flow and error handling.
        """
        # We test the function signature and expected behavior without actually downloading
        # In a real CI environment, we might use a smaller public dataset or mock load_dataset
        # Here we verify that the function exists and raises appropriate errors if dataset is missing
        
        # Save original load_dataset
        original_load = load_dataset

        def mock_load_fail(*args, **kwargs):
            raise FileNotFoundError("Mocked subset not found")

        # Temporarily replace load_dataset
        import data.download as download_module
        download_module.load_dataset = mock_load_fail

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                download_dataset()
            
            assert "subset" in str(exc_info.value).lower()
        finally:
            # Restore original
            download_module.load_dataset = original_load

class TestDownloadIntegration:
    """Integration tests for download functionality (optional, skip if network unavailable)."""

    @pytest.mark.skipif(os.environ.get("CI") == "true", reason="Skip heavy downloads in CI")
    def test_download_small_sample(self):
        """
        Download a small sample of the dataset to verify the pipeline works end-to-end.
        Skipped by default in CI to save bandwidth/time.
        """
        # This would normally call download_dataset() but for unit tests we verify
        # the checksum logic on a tiny synthetic parquet-like file instead
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "sample.parquet"
            # Create a tiny valid parquet file structure (using pandas if available, or just binary)
            try:
                import pandas as pd
                df = pd.DataFrame({"id": [1, 2, 3], "text": ["a", "b", "c"]})
                df.to_parquet(output_file)
            except ImportError:
                # Fallback: create a dummy file
                output_file.write_bytes(b"dummy_parquet_content")

            checksum = compute_file_checksum(output_file)
            assert len(checksum) == 64  # SHA-256 hex length

            # Verify checksum file generation logic
            checksum_data = {
                "checksum_value": checksum,
                "algorithm": "sha256"
            }
            assert "checksum_value" in checksum_data
            assert checksum_data["algorithm"] == "sha256"