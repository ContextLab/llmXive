import os
import sys
import tempfile
import hashlib
import pandas as pd
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from save_raw_data import compute_sha256

class TestComputeSha256:
    def test_compute_sha256_basic(self):
        """Test basic SHA256 computation on a simple file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name
        
        try:
            # Compute hash
            computed_hash = compute_sha256(temp_path)
            
            # Verify against known value
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            assert computed_hash == expected_hash
        finally:
            os.unlink(temp_path)
    
    def test_compute_sha256_binary(self):
        """Test SHA256 computation on binary data."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(b'\x00\x01\x02\x03\x04')
            temp_path = f.name
        
        try:
            computed_hash = compute_sha256(temp_path)
            expected_hash = hashlib.sha256(b'\x00\x01\x02\x03\x04').hexdigest()
            assert computed_hash == expected_hash
        finally:
            os.unlink(temp_path)
    
    def test_compute_sha256_large_file(self):
        """Test SHA256 computation on a larger file (chunked reading)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # Write 1MB of data
            f.write("x" * 1024 * 1024)
            temp_path = f.name
        
        try:
            computed_hash = compute_sha256(temp_path)
            expected_hash = hashlib.sha256(b"x" * 1024 * 1024).hexdigest()
            assert computed_hash == expected_hash
        finally:
            os.unlink(temp_path)

class TestSaveRawDataIntegration:
    def test_full_workflow(self):
        """Test the full workflow of computing and saving checksum."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test CSV file
            input_file = temp_path / "test_data.csv"
            df = pd.DataFrame({
                'sample_id': ['s1', 's2', 's3'],
                'genotype_id': ['g1', 'g2', 'g3'],
                'resistance': [1, 2, 3]
            })
            df.to_csv(input_file, index=False)
            
            # Compute checksum
            checksum = compute_sha256(str(input_file))
            
            # Write checksum file
            checksum_file = temp_path / "test_data.csv.sha256"
            with open(checksum_file, 'w') as f:
                f.write(f"{checksum}  test_data.csv\n")
            
            # Verify checksum file contents
            with open(checksum_file, 'r') as f:
                content = f.read().strip()
            
            assert content == f"{checksum}  test_data.csv"
            
            # Verify we can recompute and match
            recomputed = compute_sha256(str(input_file))
            assert recomputed == checksum