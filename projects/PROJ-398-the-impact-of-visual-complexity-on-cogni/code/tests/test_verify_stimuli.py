"""
Unit tests for verify_stimuli.py functionality.

Tests the logic of computing checksums and recording them,
using temporary directories and mock files to avoid dependency on real data downloads.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.lib.utils import compute_file_checksum
from src.metrics.verify_stimuli import verify_stimuli

class TestVerifyStimuli:
    def test_verify_stimuli_creates_file(self):
        """Test that verify_stimuli creates the output JSON file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create mock stimuli directory with a test image
            stimuli_dir = tmp_path / "data" / "stimuli"
            stimuli_dir.mkdir(parents=True)
            
            # Create a dummy image file
            test_img = stimuli_dir / "test_image.png"
            test_img.write_bytes(b"fake_image_data")
            
            # Temporarily override the global constants in the module
            import src.metrics.verify_stimuli as module_under_test
            original_stimuli_dir = module_under_test.STIMULI_DIR
            original_state_dir = module_under_test.STATE_DIR
            original_hashes_file = module_under_test.HASHES_FILE
            
            module_under_test.STIMULI_DIR = stimuli_dir
            state_dir = tmp_path / "state"
            module_under_test.STATE_DIR = state_dir
            module_under_test.HASHES_FILE = state_dir / "artifact_hashes.json"
            
            try:
                result = verify_stimuli()
                
                assert result["file_count"] == 1
                assert Path(module_under_test.HASHES_FILE).exists()
                
                with open(module_under_test.HASHES_FILE, "r") as f:
                    data = json.load(f)
                
                assert "hashes" in data
                assert "test_image.png" in data["hashes"]
                assert len(data["hashes"]["test_image.png"]) == 64  # SHA-256 hex length
            finally:
                # Restore original constants
                module_under_test.STIMULI_DIR = original_stimuli_dir
                module_under_test.STATE_DIR = original_state_dir
                module_under_test.HASHES_FILE = original_hashes_file

    def test_verify_stimuli_empty_directory(self):
        """Test behavior when stimuli directory is empty."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            stimuli_dir = tmp_path / "data" / "stimuli"
            stimuli_dir.mkdir(parents=True)
            
            state_dir = tmp_path / "state"
            
            import src.metrics.verify_stimuli as module_under_test
            original_stimuli_dir = module_under_test.STIMULI_DIR
            original_state_dir = module_under_test.STATE_DIR
            original_hashes_file = module_under_test.HASHES_FILE
            
            module_under_test.STIMULI_DIR = stimuli_dir
            module_under_test.STATE_DIR = state_dir
            module_under_test.HASHES_FILE = state_dir / "artifact_hashes.json"
            
            try:
                result = verify_stimuli()
                assert result["file_count"] == 0
                
                with open(module_under_test.HASHES_FILE, "r") as f:
                    data = json.load(f)
                
                assert data["file_count"] == 0
                assert data["hashes"] == {}
            finally:
                module_under_test.STIMULI_DIR = original_stimuli_dir
                module_under_test.STATE_DIR = original_state_dir
                module_under_test.HASHES_FILE = original_hashes_file

    def test_checksum_consistency(self):
        """Verify that the checksums computed match the utility function."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            stimuli_dir = tmp_path / "data" / "stimuli"
            stimuli_dir.mkdir(parents=True)
            
            test_content = b"test_content_for_checksum"
            test_img = stimuli_dir / "consistent_test.jpg"
            test_img.write_bytes(test_content)
            
            expected_checksum = compute_file_checksum(test_img)
            
            state_dir = tmp_path / "state"
            
            import src.metrics.verify_stimuli as module_under_test
            original_stimuli_dir = module_under_test.STIMULI_DIR
            original_state_dir = module_under_test.STATE_DIR
            original_hashes_file = module_under_test.HASHES_FILE
            
            module_under_test.STIMULI_DIR = stimuli_dir
            module_under_test.STATE_DIR = state_dir
            module_under_test.HASHES_FILE = state_dir / "artifact_hashes.json"
            
            try:
                verify_stimuli()
                
                with open(module_under_test.HASHES_FILE, "r") as f:
                    data = json.load(f)
                
                recorded_checksum = data["hashes"]["consistent_test.jpg"]
                assert recorded_checksum == expected_checksum
            finally:
                module_under_test.STIMULI_DIR = original_stimuli_dir
                module_under_test.STATE_DIR = original_state_dir
                module_under_test.HASHES_FILE = original_hashes_file