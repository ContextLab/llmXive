"""
Unit tests for the reproducibility check script.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import hashlib

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

# Mock the generator module if it doesn't exist
# This allows the test to run even if T011 is not done
class MockGenerator:
    @staticmethod
    def generate_dataset(seed: int, output_dir: str):
        """Mock generator that creates a deterministic CSV."""
        output_path = Path(output_dir) / "mock_data.csv"
        content = f"seed,{seed}\nrow,1\n"
        with open(output_path, "w") as f:
            f.write(content)

# Mock the import
sys.modules['generators'] = type(sys)('generators')
sys.modules['generators.logic_generator'] = MockGenerator

from utils.reproducibility_check import compute_sha256

def test_compute_sha256():
    """Test SHA256 computation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        checksum = compute_sha256(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

        # Verify with known value
        import hashlib
        expected = hashlib.sha256(b"test data").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_sha256_different_files():
    """Test that different files have different checksums."""
    with tempfile.NamedTemporaryFile(delete=False) as f1:
        f1.write(b"data1")
        path1 = f1.name

    with tempfile.NamedTemporaryFile(delete=False) as f2:
        f2.write(b"data2")
        path2 = f2.name

    try:
        checksum1 = compute_sha256(path1)
        checksum2 = compute_sha256(path2)
        assert checksum1 != checksum2
    finally:
        os.unlink(path1)
        os.unlink(path2)