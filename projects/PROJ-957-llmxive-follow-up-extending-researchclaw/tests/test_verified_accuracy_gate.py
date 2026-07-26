"""
Tests for the Verified Accuracy Gate (Task T007b)

These tests verify the gate logic for data integrity checking.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config
from utils.checksum import write_checksum


class TestVerifiedAccuracyGate:
    """Tests for the Verified Accuracy Gate logic."""
    
    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project directory structure."""
        # Create directory structure
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        yield tmp_path
        
        # Cleanup handled by tmp_path
    
    def test_gate_passes_with_matching_checksum(self, temp_project_dir):
        """Test that gate passes when checksum matches expected value."""
        # Setup: Create a checksum file with the expected value
        config = Config.load()
        checksum_file = temp_project_dir / "data" / "raw" / "checksum.txt"
        
        # Write the expected checksum
        write_checksum(checksum_file, config.EXPECTED_DATASET_CHECKSUM)
        
        # Import the gate logic
        import sys
        from run_verified_accuracy_gate import main as gate_main
        
        # Temporarily change working directory
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Run the gate
            result = gate_main()
            
            # Assert pass
            assert result == 0, "Gate should return 0 on success"
            
            # Verify files created
            log_file = temp_project_dir / "results" / "verified_accuracy_gate.log"
            done_marker = temp_project_dir / "results" / "verified_accuracy_gate.done"
            failed_marker = temp_project_dir / "results" / "verified_accuracy_gate.failed"
            
            assert log_file.exists(), "Log file should be created"
            assert done_marker.exists(), "Done marker should be created"
            assert not failed_marker.exists(), "Failed marker should not exist"
            
            # Verify log content
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "GATE: Verified Accuracy [PASS]" in content
        finally:
            os.chdir(original_cwd)
    
    def test_gate_fails_with_mismatched_checksum(self, temp_project_dir):
        """Test that gate fails when checksum does not match."""
        # Setup: Create a checksum file with a WRONG value
        checksum_file = temp_project_dir / "data" / "raw" / "checksum.txt"
        write_checksum(checksum_file, "wrong_checksum_value_12345")
        
        # Import the gate logic
        import sys
        from run_verified_accuracy_gate import main as gate_main
        
        # Temporarily change working directory
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Run the gate
            result = gate_main()
            
            # Assert fail
            assert result == 1, "Gate should return 1 on failure"
            
            # Verify files created
            log_file = temp_project_dir / "results" / "verified_accuracy_gate.log"
            done_marker = temp_project_dir / "results" / "verified_accuracy_gate.done"
            failed_marker = temp_project_dir / "results" / "verified_accuracy_gate.failed"
            
            assert log_file.exists(), "Log file should be created"
            assert failed_marker.exists(), "Failed marker should be created"
            assert not done_marker.exists(), "Done marker should not exist"
            
            # Verify log content
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "GATE: Verified Accuracy [FAIL]" in content
        finally:
            os.chdir(original_cwd)
    
    def test_gate_fails_with_missing_checksum_file(self, temp_project_dir):
        """Test that gate fails when checksum file is missing."""
        # Setup: Do not create the checksum file
        
        # Import the gate logic
        import sys
        from run_verified_accuracy_gate import main as gate_main
        
        # Temporarily change working directory
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Run the gate
            result = gate_main()
            
            # Assert fail
            assert result == 1, "Gate should return 1 when file is missing"
            
            # Verify files created
            log_file = temp_project_dir / "results" / "verified_accuracy_gate.log"
            failed_marker = temp_project_dir / "results" / "verified_accuracy_gate.failed"
            
            assert log_file.exists(), "Log file should be created"
            assert failed_marker.exists(), "Failed marker should be created"
        finally:
            os.chdir(original_cwd)
