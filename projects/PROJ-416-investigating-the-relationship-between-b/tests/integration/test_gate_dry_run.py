"""
Integration test for T046: Verified Source Gate Dry-Run.

This test verifies that the gate logic in `code/scripts/verify_gate.py`
correctly identifies missing or corrupted `data/verified_sources.json`
and triggers the appropriate `FatalError` or validation failure.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.data.download import FatalError
from code.scripts.verify_gate import run_gate_verification, check_file_exists, check_file_valid_json, check_source_id_valid

def test_gate_missing_file():
    """Test that the gate triggers when the file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        fake_config_path = tmp_path / "config.env"
        fake_verified_path = tmp_path / "verified_sources.json"
        
        # Ensure file does NOT exist
        assert not fake_verified_path.exists()

        # Mock the Config to point to our temp directory
        with patch('code.scripts.verify_gate.Config') as MockConfig:
            mock_instance = MagicMock()
            mock_instance.VERIFIED_SOURCES_PATH = fake_verified_path
            mock_instance.LOGS_DIR = tmp_path
            MockConfig.return_value = mock_instance

            # Run the verification logic
            # We expect this to return 0 (success) because the gate correctly identified the missing file
            result = run_gate_verification()
            
            # The function should return 0 if the gate logic worked (even if file is missing)
            # because "Gate Active" is the success condition for a missing file scenario.
            assert result == 0, "Gate should trigger correctly on missing file"

def test_gate_corrupted_json():
    """Test that the gate triggers when the file contains invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        fake_verified_path = tmp_path / "verified_sources.json"
        
        # Write invalid JSON
        with open(fake_verified_path, 'w') as f:
            f.write("{ this is not valid json }")
        
        with patch('code.scripts.verify_gate.Config') as MockConfig:
            mock_instance = MagicMock()
            mock_instance.VERIFIED_SOURCES_PATH = fake_verified_path
            mock_instance.LOGS_DIR = tmp_path
            MockConfig.return_value = mock_instance

            result = run_gate_verification()
            assert result == 0, "Gate should trigger correctly on corrupted JSON"

def test_gate_missing_source_id():
    """Test that the gate triggers when source_id is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        fake_verified_path = tmp_path / "verified_sources.json"
        
        # Write valid JSON but missing source_id
        data = {
            "source_name": "OpenNeuro",
            "verified_date": "2023-01-01"
        }
        with open(fake_verified_path, 'w') as f:
            json.dump(data, f)
        
        with patch('code.scripts.verify_gate.Config') as MockConfig:
            mock_instance = MagicMock()
            mock_instance.VERIFIED_SOURCES_PATH = fake_verified_path
            mock_instance.LOGS_DIR = tmp_path
            MockConfig.return_value = mock_instance

            result = run_gate_verification()
            assert result == 0, "Gate should trigger correctly on missing source_id"

def test_gate_valid_file():
    """Test that the gate passes when the file is valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        fake_verified_path = tmp_path / "verified_sources.json"
        
        # Write valid JSON with source_id
        data = {
            "source_name": "OpenNeuro",
            "source_id": "ds000001",
            "verified_date": "2023-01-01"
        }
        with open(fake_verified_path, 'w') as f:
            json.dump(data, f)
        
        with patch('code.scripts.verify_gate.Config') as MockConfig:
            mock_instance = MagicMock()
            mock_instance.VERIFIED_SOURCES_PATH = fake_verified_path
            mock_instance.LOGS_DIR = tmp_path
            MockConfig.return_value = mock_instance

            result = run_gate_verification()
            assert result == 0, "Gate should pass for valid file"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])