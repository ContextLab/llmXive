import pytest
import os
import csv
from pathlib import Path
import hashlib
import sys
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from checksum_pool import main
from utils.checksum_utils import compute_sha256

class TestChecksumPool:
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        # Create necessary directories
        data_processed = Path(temp_dir) / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Create a dummy full_pool_final.csv
        csv_path = data_processed / "full_pool_final.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["material_id", "composition", "formation_energy"])
            writer.writeheader()
            writer.writerow({"material_id": "mp-1", "composition": "H2O", "formation_energy": "-1.0"})
            writer.writerow({"material_id": "mp-2", "composition": "CO2", "formation_energy": "-2.0"})
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_checksum_generation(self, temp_project_dir):
        """Test that T028 generates a valid checksum file."""
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)
            
            # Run main
            result = main()
            
            assert result == 0, "main() should return 0 on success"
            
            # Verify checksum file exists
            checksum_file = Path(temp_project_dir) / "data" / "processed" / "full_pool_final.csv.sha256"
            assert checksum_file.exists(), "Checksum file should exist"
            
            # Verify checksum content
            with open(checksum_file, 'r') as f:
                stored_checksum = f.read().strip()
            
            # Compute expected checksum
            csv_file = Path(temp_project_dir) / "data" / "processed" / "full_pool_final.csv"
            expected_checksum = compute_sha256(csv_file)
            
            assert stored_checksum == expected_checksum, f"Checksum mismatch: {stored_checksum} != {expected_checksum}"
            
        finally:
            os.chdir(original_cwd)

    def test_missing_input_file(self, temp_project_dir):
        """Test that T028 fails gracefully if input file is missing."""
        # Remove the input file
        csv_path = Path(temp_project_dir) / "data" / "processed" / "full_pool_final.csv"
        csv_path.unlink()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)
            
            result = main()
            
            assert result == 1, "main() should return 1 if input file is missing"
            
        finally:
            os.chdir(original_cwd)