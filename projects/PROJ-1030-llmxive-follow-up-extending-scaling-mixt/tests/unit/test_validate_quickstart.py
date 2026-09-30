"""
Unit tests for the Quickstart Validation Script (T038).
"""
import os
import sys
import tempfile
import json
import hashlib
from pathlib import Path
from unittest import mock
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import validate_quickstart

def test_check_file_exists_missing():
    """Test that check_file_exists returns False for missing files."""
    fake_path = Path("/nonexistent/file.txt")
    passed, msg = validate_quickstart.check_file_exists(fake_path, "Test File")
    assert passed is False
    assert "Missing" in msg

def test_check_file_exists_empty():
    """Test that check_file_exists returns False for empty files."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
        # File is created but empty
    
    try:
        passed, msg = validate_quickstart.check_file_exists(tmp_path, "Test Empty File")
        assert passed is False
        assert "Empty" in msg
    finally:
        tmp_path.unlink()

def test_check_file_exists_ok():
    """Test that check_file_exists returns True for valid files."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
        tmp.write("content")
        tmp_path = Path(tmp.name)
    
    try:
        passed, msg = validate_quickstart.check_file_exists(tmp_path, "Test Valid File")
        assert passed is True
        assert "OK" in msg
    finally:
        tmp_path.unlink()

def test_dry_run_imports_syntax_error():
    """Test dry_run_imports with a module that has a syntax error."""
    # Create a temp file with syntax error
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, dir=str(PROJECT_ROOT)) as tmp:
        tmp.write(b"def broken(:") # Syntax error
        tmp_path = Path(tmp.name)
        module_name = tmp_path.stem

    try:
        # Mock sys.path to include the temp file
        with mock.patch.object(validate_quickstart.sys, 'path', [str(PROJECT_ROOT)] + validate_quickstart.sys.path):
            # Temporarily add the bad module to the list
            original_modules = validate_quickstart.CRITICAL_MODULES
            validate_quickstart.CRITICAL_MODULES = [module_name]
            
            try:
                passed, msg = validate_quickstart.dry_run_imports()
                assert passed is False
                assert "Syntax error" in msg
            finally:
                validate_quickstart.CRITICAL_MODULES = original_modules
    finally:
        tmp_path.unlink()

def test_verify_checksums_success():
    """Test verify_checksums with a valid manifest and matching files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        content = b"hello world"
        test_file.write_bytes(content)
        
        # Calculate hash
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Create manifest
        manifest_data = {
            "files": [
                {"path": "test_file.txt", "sha256": sha256_hash}
            ]
        }
        manifest_file = state_dir / "manifest.yaml"
        import yaml
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest_data, f)
        
        # Mock the global variables
        original_state_dir = validate_quickstart.STATE_DIR
        original_project_root = validate_quickstart.PROJECT_ROOT
        
        try:
            validate_quickstart.STATE_DIR = state_dir
            validate_quickstart.PROJECT_ROOT = tmp_path
            
            passed, msg = validate_quickstart.verify_checksums()
            assert passed is True
            assert "verified" in msg
        finally:
            validate_quickstart.STATE_DIR = original_state_dir
            validate_quickstart.PROJECT_ROOT = original_project_root

def test_verify_checksums_mismatch():
    """Test verify_checksums with a mismatched hash."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        content = b"hello world"
        test_file.write_bytes(content)
        
        # Create manifest with WRONG hash
        manifest_data = {
            "files": [
                {"path": "test_file.txt", "sha256": "wronghash123"}
            ]
        }
        manifest_file = state_dir / "manifest.yaml"
        import yaml
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest_data, f)
        
        # Mock the global variables
        original_state_dir = validate_quickstart.STATE_DIR
        original_project_root = validate_quickstart.PROJECT_ROOT
        
        try:
            validate_quickstart.STATE_DIR = state_dir
            validate_quickstart.PROJECT_ROOT = tmp_path
            
            passed, msg = validate_quickstart.verify_checksums()
            assert passed is False
            assert "mismatch" in msg
        finally:
            validate_quickstart.STATE_DIR = original_state_dir
            validate_quickstart.PROJECT_ROOT = original_project_root