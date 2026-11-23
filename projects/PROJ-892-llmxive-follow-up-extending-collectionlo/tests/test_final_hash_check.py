"""
Unit tests for code/final_hash_check.py
"""
import os
import sys
import json
import hashlib
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))

from final_hash_check import (
    compute_sha256_file,
    load_artifacts_state,
    save_artifacts_state,
    validate_artifact_entry,
    collect_expected_artifacts,
    run_final_hash_check,
    get_project_root
)

def test_compute_sha256_file():
    """Test SHA-256 computation on a temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_value = compute_sha256_file(temp_path)
        assert len(hash_value) == 64  # SHA-256 hex length
        assert isinstance(hash_value, str)
    finally:
        temp_path.unlink()

def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256_file(Path("/nonexistent/file.txt"))

def test_load_artifacts_state():
    """Test loading a valid artifacts.yaml file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({'artifacts': {'test': {'path': 'test.txt', 'hash': 'abc123'}}}, f)
        temp_path = Path(f.name)
    
    try:
        data = load_artifacts_state(temp_path)
        assert 'artifacts' in data
        assert data['artifacts']['test']['path'] == 'test.txt'
    finally:
        temp_path.unlink()

def test_load_artifacts_state_not_found():
    """Test that FileNotFoundError is raised for missing state file."""
    with pytest.raises(FileNotFoundError):
        load_artifacts_state(Path("/nonexistent/state.yaml"))

def test_save_artifacts_state():
    """Test saving artifacts to a YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / 'artifacts.yaml'
        data = {'artifacts': {'test': {'path': 'test.txt', 'hash': 'abc123'}}}
        
        save_artifacts_state(state_path, data)
        
        assert state_path.exists()
        with open(state_path, 'r') as f:
            loaded = yaml.safe_load(f)
        assert loaded == data

def test_validate_artifact_entry_valid():
    """Test validation of a valid artifact."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        expected_hash = compute_sha256_file(temp_path)
        is_valid = validate_artifact_entry("test", temp_path, expected_hash)
        assert is_valid is True
    finally:
        temp_path.unlink()

def test_validate_artifact_entry_hash_mismatch():
    """Test validation with a hash mismatch."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        is_valid = validate_artifact_entry("test", temp_path, "wrong_hash")
        assert is_valid is False
    finally:
        temp_path.unlink()

def test_validate_artifact_entry_not_found():
    """Test validation of a missing artifact."""
    is_valid = validate_artifact_entry("test", Path("/nonexistent/file.txt"), "any_hash")
    assert is_valid is False

def test_collect_expected_artifacts():
    """Test collection of expected artifacts from state data."""
    state_data = {
        'artifacts': {
            'valid_artifact': {'path': 'data/test.txt', 'hash': 'abc123'},
            'missing_path': 'just_a_hash',  # Should be skipped
            'invalid_entry': None
        }
    }
    
    artifacts = collect_expected_artifacts(state_data)
    assert len(artifacts) == 1
    assert artifacts[0]['name'] == 'valid_artifact'
    assert artifacts[0]['path'] == 'data/test.txt'

def test_run_final_hash_check_success():
    """Test successful final hash check with all valid artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a mock state file
        state_data = {
            'artifacts': {
                'test_artifact': {
                    'path': 'data/test.txt',
                    'hash': 'placeholder'
                }
            }
        }
        
        # Create the actual artifact file
        artifact_dir = tmpdir_path / 'data'
        artifact_dir.mkdir()
        artifact_file = artifact_dir / 'test.txt'
        artifact_file.write_text("test content")
        
        # Update hash
        actual_hash = compute_sha256_file(artifact_file)
        state_data['artifacts']['test_artifact']['hash'] = actual_hash
        
        # Write state file
        state_file = tmpdir_path / 'state' / 'artifacts.yaml'
        state_file.parent.mkdir()
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)
        
        # Mock get_project_root to return our temp directory
        with patch('final_hash_check.get_project_root', return_value=tmpdir_path):
            with patch('final_hash_check.logging'):  # Suppress logging
                result = run_final_hash_check()
                assert result is True

def test_run_final_hash_check_missing_artifact():
    """Test final hash check with a missing artifact."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create state file with reference to non-existent artifact
        state_data = {
            'artifacts': {
                'missing_artifact': {
                    'path': 'data/nonexistent.txt',
                    'hash': 'abc123'
                }
            }
        }
        
        state_file = tmpdir_path / 'state' / 'artifacts.yaml'
        state_file.parent.mkdir()
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)
        
        with patch('final_hash_check.get_project_root', return_value=tmpdir_path):
            with patch('final_hash_check.logging'):
                result = run_final_hash_check()
                assert result is False

def test_run_final_hash_check_hash_mismatch():
    """Test final hash check with a hash mismatch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create artifact file
        artifact_dir = tmpdir_path / 'data'
        artifact_dir.mkdir()
        artifact_file = artifact_dir / 'test.txt'
        artifact_file.write_text("test content")
        
        # Create state file with wrong hash
        state_data = {
            'artifacts': {
                'test_artifact': {
                    'path': 'data/test.txt',
                    'hash': 'wrong_hash'
                }
            }
        }
        
        state_file = tmpdir_path / 'state' / 'artifacts.yaml'
        state_file.parent.mkdir()
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)
        
        with patch('final_hash_check.get_project_root', return_value=tmpdir_path):
            with patch('final_hash_check.logging'):
                result = run_final_hash_check()
                assert result is False