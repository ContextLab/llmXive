import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.checksum_utils import generate_and_save_checksum, compute_sha256

class TestChecksumPool:
    """Tests for T028: Checksum generation and verification."""

    def test_compute_sha256(self):
        """Test that compute_sha256 returns a valid hex digest."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("id,value\n1,10\n2,20\n")
            temp_path = Path(f.name)

        try:
            checksum = compute_sha256(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            temp_path.unlink()

    def test_generate_and_save_checksum(self):
        """Test that generate_and_save_checksum creates the .sha256 file with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "test_data.csv"
            checksum_path = Path(tmpdir) / "test_data.csv.sha256"
            
            # Write test data
            with open(data_path, 'w') as f:
                f.write("id,value\n1,10\n2,20\n")
            
            # Generate checksum
            generate_and_save_checksum(data_path, checksum_path)
            
            # Verify file exists
            assert checksum_path.exists()
            
            # Verify content format: "<hash>  <filename>"
            with open(checksum_path, 'r') as f:
                content = f.read().strip()
            
            parts = content.split()
            assert len(parts) == 2
            assert len(parts[0]) == 64  # Hash length
            assert parts[1] == data_path.name

    def test_integration_flow(self):
        """Simulate the T028 flow: create CSV, generate checksum, verify integrity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "full_pool_final.csv"
            checksum_path = Path(tmpdir) / "full_pool_final.csv.sha256"
            
            # Simulate T027 output
            with open(data_path, 'w') as f:
                f.write("material_id,composition,formation_energy,dft_computed\n")
                f.write("mp-1,Fe,0.1,True\n")
                f.write("mp-2,Ni,0.2,True\n")
                f.write("mp-3,Cu,0.3,True\n")
            
            # Run T028 logic
            generate_and_save_checksum(data_path, checksum_path)
            
            # Verify
            with open(checksum_path, 'r') as f:
                stored_checksum = f.read().strip().split()[0]
            
            computed_checksum = compute_sha256(data_path)
            assert stored_checksum == computed_checksum