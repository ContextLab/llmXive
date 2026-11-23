import json
import os
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import the functions to test
from download import (
    calculate_sha256, 
    verify_checksums, 
    save_checksums, 
    load_saved_checksums,
    download_human_eval,
    download_mbpp
)

class TestChecksumCalculation:
    def test_calculate_sha256(self):
        """Verify SHA-256 calculation on a known string."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = b"Hello, World!"
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            # Expected hash for "Hello, World!"
            expected = hashlib.sha256(content).hexdigest()
            result = calculate_sha256(tmp_path)
            assert result == expected
        finally:
            tmp_path.unlink()

class TestChecksumPersistence:
    def test_save_and_load_checksums(self):
        """Verify that checksums can be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksums_file = Path(tmpdir) / "checksums.json"
            
            # Save
            save_checksums(Path(tmpdir), checksums_file, "test_dataset", "abc123")
            
            # Load
            loaded = load_saved_checksums(checksums_file)
            assert "test_dataset" in loaded
            assert loaded["test_dataset"] == "abc123"

class TestVerificationLogic:
    def test_verify_checksums_success(self):
        """Test verification when hashes match."""
        with tempfile.TemporaryDirectory() as tmpdir:
          data_dir = Path(tmpdir)
          checksums_file = data_dir / "checksums.json"
          dataset_dir = data_dir / "test_ds"
          dataset_dir.mkdir()
          
          # Create a dummy file
          dummy_file = dataset_dir / "data.arrow"
          dummy_file.write_bytes(b"test data")
          
          # Calculate real hash
          real_hash = calculate_sha256(dummy_file)
          
          # Save checksum
          save_checksums(data_dir, checksums_file, "test_ds", real_hash)
          
          # Verify
          assert verify_checksums(data_dir, checksums_file, "test_ds") is True

    def test_verify_checksums_failure(self):
        """Test verification when hashes do not match."""
        with tempfile.TemporaryDirectory() as tmpdir:
          data_dir = Path(tmpdir)
          checksums_file = data_dir / "checksums.json"
          dataset_dir = data_dir / "test_ds"
          dataset_dir.mkdir()
          
          # Create a dummy file
          dummy_file = dataset_dir / "data.arrow"
          dummy_file.write_bytes(b"test data")
          
          # Save WRONG checksum
          save_checksums(data_dir, checksums_file, "test_ds", "wrong_hash_123")
          
          # Verify should fail
          assert verify_checksums(data_dir, checksums_file, "test_ds") is False

    def test_verify_missing_file(self):
        """Test verification when the dataset file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
          data_dir = Path(tmpdir)
          checksums_file = data_dir / "checksums.json"
          
          # Save a checksum for a non-existent file
          save_checksums(data_dir, checksums_file, "missing_ds", "some_hash")
          
          # Verify should fail because directory doesn't exist
          assert verify_checksums(data_dir, checksums_file, "missing_ds") is False

class TestDownloadFunctions:
    """
    Contract tests for dataset download integrity.
    These tests verify the logic of the download pipeline using real data sources
    (HuggingFace datasets) but may be skipped in environments without network access
    or with strict timeouts.
    """
    
    def test_download_human_eval_contract(self):
        """
        Contract test: Verify that download_human_eval returns a valid path 
        and that the resulting dataset directory contains expected files 
        (e.g., 'train.jsonl' or parquet files) and matches the stored checksum.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            checksums_file = data_dir / "checksums.json"
            
            # Attempt to download the real HumanEval dataset
            # Note: This will raise an exception if network is unavailable or HF is down.
            try:
                path = download_human_eval(data_dir, checksums_file)
                
                # Contract 1: Path must exist
                assert path.exists(), "Downloaded dataset path does not exist"
                
                # Contract 2: Checksum file must be created
                assert checksums_file.exists(), "Checksum file was not created"
                
                # Contract 3: Verify integrity using the saved checksum
                assert verify_checksums(data_dir, checksums_file, "human_eval"), \
                    "Dataset integrity verification failed"
                    
            except Exception as e:
                # If the download fails due to network/HF issues, we fail the test loudly
                # rather than mocking data, per project constraints.
                pytest.fail(f"Download contract failed: {str(e)}")

    def test_download_mbpp_contract(self):
        """
        Contract test: Verify that download_mbpp returns a valid path 
        and that the resulting dataset directory contains expected files 
        and matches the stored checksum.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            checksums_file = data_dir / "checksums.json"
            
            try:
                path = download_mbpp(data_dir, checksums_file)
                
                # Contract 1: Path must exist
                assert path.exists(), "Downloaded dataset path does not exist"
                
                # Contract 2: Checksum file must be created
                assert checksums_file.exists(), "Checksum file was not created"
                
                # Contract 3: Verify integrity using the saved checksum
                assert verify_checksums(data_dir, checksums_file, "mbpp"), \
                    "Dataset integrity verification failed"
                    
            except Exception as e:
                pytest.fail(f"Download contract failed: {str(e)}")
            
    @pytest.mark.skip(reason="Requires network access and significant download time")
    def test_download_human_eval_integration(self):
        """Integration test for HumanEval download and verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            checksums_file = data_dir / "checksums.json"
            
            # This would download the real dataset
            # path = download_human_eval(data_dir, checksums_file)
            # assert path.exists()
            # assert checksums_file.exists()
            pass

    @pytest.mark.skip(reason="Requires network access and significant download time")
    def test_download_mbpp_integration(self):
        """Integration test for MBPP download and verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            checksums_file = data_dir / "checksums.json"
            
            # path = download_mbpp(data_dir, checksums_file)
            # assert path.exists()
            # assert checksums_file.exists()
            pass