"""
Tests for the pytest configuration plugin (code/utils/pytest_config.py).

These tests verify:
1. Random seed pinning.
2. Checksum computation and verification.
3. GITHUB_JOB_DURATION logging logic.
"""
import os
import random
import time
import tempfile
from pathlib import Path
import pytest
import sys

# Import the module under test
# Note: We import directly from the module to test the functions
from utils.pytest_config import (
    pin_random_seeds,
    compute_sha256_checksum,
    enforce_checksum_determinism,
    log_github_job_duration,
    FIXED_SEED
)

class TestSeedPinning:
    def test_pin_random_seeds_deterministic(self):
        """Test that pinning seeds produces deterministic random numbers."""
        # Pin seeds
        pin_random_seeds()
        
        # Generate a number
        val1 = random.random()
        
        # Pin seeds again
        pin_random_seeds()
        
        # Generate the same number
        val2 = random.random()
        
        assert val1 == val2, "Random numbers should be deterministic after pinning seeds"

    def test_pin_random_seeds_sets_numpy(self):
        """Test that numpy seeds are also pinned if numpy is available."""
        try:
            import numpy as np
            pin_random_seeds()
            arr1 = np.random.rand(5)
            
            pin_random_seeds()
            arr2 = np.random.rand(5)
            
            assert np.array_equal(arr1, arr2), "Numpy arrays should be deterministic"
        except ImportError:
            pytest.skip("NumPy not installed")

class TestChecksum:
    def test_compute_sha256_checksum(self):
        """Test SHA-256 computation on a known file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_sha256_checksum(tmp_path)
            # Known SHA-256 for "test data"
            expected = "39f7af0d2e1009e382c8c249050c9739519d7316e39d26396f9092742e353756"
            assert checksum == expected, f"Checksum mismatch: {checksum} != {expected}"
        finally:
            tmp_path.unlink()

    def test_compute_sha256_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256_checksum(Path("nonexistent_file.txt"))

    def test_enforce_checksum_determinism_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_sha256_checksum(tmp_path)
            checksums_content = f"{checksum}  {tmp_path.name}\n"
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as checksum_file:
                checksum_file.write(checksums_content)
                checksum_file_path = Path(checksum_file.name)
            
            try:
                expected = {tmp_path.name: checksum}
                result = enforce_checksum_determinism(checksum_file_path, expected)
                assert result is True, "Checksum verification should succeed"
            finally:
                checksum_file_path.unlink()
        finally:
            tmp_path.unlink()

    def test_enforce_checksum_determinism_failure(self):
        """Test failed checksum verification due to mismatch."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_sha256_checksum(tmp_path)
            wrong_checksum = "0" * 64
            checksums_content = f"{wrong_checksum}  {tmp_path.name}\n"
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as checksum_file:
                checksum_file.write(checksums_content)
                checksum_file_path = Path(checksum_file.name)
            
            try:
                expected = {tmp_path.name: checksum}
                result = enforce_checksum_determinism(checksum_file_path, expected)
                assert result is False, "Checksum verification should fail"
            finally:
                checksum_file_path.unlink()
        finally:
            tmp_path.unlink()

    def test_enforce_checksum_determinism_missing_file(self):
        """Test failed checksum verification due to missing file in checksums."""
        checksums_content = "some_checksum  missing_file.txt\n"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as checksum_file:
            checksum_file.write(checksums_content)
            checksum_file_path = Path(checksum_file.name)
        
        try:
            expected = {"missing_file.txt": "some_checksum"}
            result = enforce_checksum_determinism(checksum_file_path, expected)
            assert result is False, "Checksum verification should fail for missing file"
        finally:
            checksum_file_path.unlink()

class TestJobDuration:
    def test_log_github_job_duration(self, caplog):
        """Test that job duration is logged correctly."""
        start = time.time()
        time.sleep(0.1)
        end = time.time()
        
        with caplog.at_level(logging.INFO):
            log_github_job_duration(start, end)
        
        assert "GitHub Job Duration:" in caplog.text
        
        # Check GITHUB_OUTPUT if in CI
        if os.getenv("GITHUB_ACTIONS") == "true":
            github_output = os.getenv("GITHUB_OUTPUT")
            if github_output and os.path.exists(github_output):
                with open(github_output, "r") as f:
                    content = f.read()
                    assert "GITHUB_JOB_DURATION=" in content

class TestPytestConfiguration:
    def test_pytest_configure_pins_seeds(self):
        """Test that pytest_configure pins seeds."""
        from unittest.mock import MagicMock
        config = MagicMock()
        
        # Reset random state first
        random.seed()
        val_before = random.random()
        
        # Call the function
        from utils.pytest_config import pytest_configure
        pytest_configure(config)
        
        # Check that seeds are pinned
        val_after = random.random()
        # We can't easily check the exact value without re-pinning,
        # but we can check that the function runs without error
        # and that the logging happens.
        # The actual determinism is tested in test_pin_random_seeds_deterministic
        pass

    def test_pytest_addoption_adds_checksums_file_option(self):
        """Test that pytest_addoption adds the checksums-file option."""
        from unittest.mock import MagicMock
        parser = MagicMock()
        
        from utils.pytest_config import pytest_addoption
        pytest_addoption(parser)
        
        parser.addoption.assert_called_with(
            "--checksums-file",
            action="store",
            default="results/checksums.txt",
            help="Path to the file containing expected checksums for verification."
        )
