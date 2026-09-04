"""
Tests for the checksums module (T014).
"""
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust import based on project structure if running from root
try:
    from code.checksums import (
        ensure_state_file_exists,
        load_state,
        save_state,
        record_checksums,
        verify_checksums,
        PROJECT_ROOT
    )
except ImportError:
    # Fallback for direct execution in some environments
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from checksums import (
        ensure_state_file_exists,
        load_state,
        save_state,
        record_checksums,
        verify_checksums,
        PROJECT_ROOT
    )


@pytest.fixture
def temp_state_dir(tmp_path):
    """Creates a temporary directory structure mimicking the project state."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return state_dir


@pytest.fixture
def temp_test_file(tmp_path):
    """Creates a temporary file with known content for checksumming."""
    test_file = tmp_path / "test_data.txt"
    test_file.write_text("Hello, World! This is a test file for checksum verification.")
    return test_file


def test_ensure_state_file_exists_creates_file(temp_state_dir):
    """Test that ensure_state_file_exists creates the YAML file if missing."""
    # Mock PROJECT_ROOT to point to temp directory for this test
    # We need to patch the module-level variable
    with patch('code.checksums.PROJECT_ROOT', temp_state_dir.parent.parent):
        with patch('code.checksums.STATE_FILE_PATH', temp_state_dir / "PROJ-268-test.yaml"):
            result_path = ensure_state_file_exists()
            assert result_path.exists()
            
            # Check content structure
            with open(result_path, 'r') as f:
                data = yaml.safe_load(f)
            assert "project_id" in data
            assert "artifacts" in data


def test_record_checksums_updates_state(temp_test_file, tmp_path):
    """Test that record_checksums correctly computes and saves checksums."""
    # Setup temp state file path
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "PROJ-268-test.yaml"
    
    with patch('code.checksums.PROJECT_ROOT', tmp_path):
        with patch('code.checksums.STATE_FILE_PATH', state_file):
            # Record checksum
            result = record_checksums([str(temp_test_file)], "test_batch", "Test batch description")
            
            assert len(result) == 1
            assert str(temp_test_file.relative_to(tmp_path)) in result
            
            # Verify state file content
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            
            assert "test_batch" in state["artifacts"]
            assert "entries" in state["artifacts"]["test_batch"]
            assert str(temp_test_file.relative_to(tmp_path)) in state["artifacts"]["test_batch"]["entries"]
            
            entry = state["artifacts"]["test_batch"]["entries"][str(temp_test_file.relative_to(tmp_path))]
            assert "checksum" in entry
            assert "timestamp" in entry


def test_verify_checksums_valid(temp_test_file, tmp_path):
    """Test verify_checksums returns True for valid files."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "PROJ-268-test.yaml"
    
    with patch('code.checksums.PROJECT_ROOT', tmp_path):
        with patch('code.checksums.STATE_FILE_PATH', state_file):
            # First record
            record_checksums([str(temp_test_file)], "verify_test")
            
            # Then verify
            is_valid = verify_checksums("verify_test")
            assert is_valid is True


def test_verify_checksums_invalid(temp_test_file, tmp_path):
    """Test verify_checksums returns False when file content changes."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "PROJ-268-test.yaml"
    
    with patch('code.checksums.PROJECT_ROOT', tmp_path):
        with patch('code.checksums.STATE_FILE_PATH', state_file):
            # Record initial state
            record_checksums([str(temp_test_file)], "verify_test_invalid")
            
            # Modify file
            temp_test_file.write_text("Modified content")
            
            # Verify should fail
            is_valid = verify_checksums("verify_test_invalid")
            assert is_valid is False