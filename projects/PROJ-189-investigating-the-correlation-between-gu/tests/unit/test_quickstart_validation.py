"""
Unit tests for quickstart_validation.py
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
# Note: We assume the functions are importable from the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from quickstart_validation import run_script, verify_artifact, verify_json_content

def test_run_script_success():
    """Test run_script with a successful command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        result = run_script("test_script.py", ["--arg1"])
        assert result is True
        mock_run.assert_called_once()

def test_run_script_failure():
    """Test run_script with a failed command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        result = run_script("test_script.py")
        assert result is False

def test_run_script_timeout():
    """Test run_script with a timeout."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Timeout") # Simplified for test
        result = run_script("test_script.py")
        assert result is False

def test_verify_artifact_exists():
    """Test verify_artifact when file exists."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name
    
    try:
        # Adjust path to be relative to project root logic if needed, 
        # but here we test the logic directly
        # The function expects a path relative to PROJECT_ROOT
        # For unit test, we mock the PROJECT_ROOT behavior or pass absolute
        # Since the function does `PROJECT_ROOT / path_str`, we need to be careful.
        # Let's test the logic by patching the path check.
        
        with patch('quickstart_validation.PROJECT_ROOT', Path(tmp_path).parent):
            file_name = Path(tmp_path).name
            result = verify_artifact(file_name, must_exist=True, min_size_bytes=0)
            assert result is True
    finally:
        os.unlink(tmp_path)

def test_verify_artifact_missing():
    """Test verify_artifact when file is missing."""
    result = verify_artifact("non_existent_file.txt", must_exist=True)
    assert result is False

def test_verify_artifact_too_small():
    """Test verify_artifact when file is too small."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"x") # 1 byte
        tmp_path = tmp.name
    
    try:
        with patch('quickstart_validation.PROJECT_ROOT', Path(tmp_path).parent):
            file_name = Path(tmp_path).name
            result = verify_artifact(file_name, must_exist=True, min_size_bytes=100)
            assert result is False
    finally:
        os.unlink(tmp_path)

def test_verify_json_content_valid():
    """Test verify_json_content with valid JSON and keys."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump({"key1": "value1", "key2": 123}, tmp)
        tmp_path = tmp.name
    
    try:
        with patch('quickstart_validation.PROJECT_ROOT', Path(tmp_path).parent):
            file_name = Path(tmp_path).name
            result = verify_json_content(file_name, required_keys=["key1"])
            assert result is True
    finally:
        os.unlink(tmp_path)

def test_verify_json_content_missing_keys():
    """Test verify_json_content with missing required keys."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump({"key1": "value1"}, tmp)
        tmp_path = tmp.name
    
    try:
        with patch('quickstart_validation.PROJECT_ROOT', Path(tmp_path).parent):
            file_name = Path(tmp_path).name
            result = verify_json_content(file_name, required_keys=["key1", "missing_key"])
            assert result is False
    finally:
        os.unlink(tmp_path)

def test_verify_json_invalid():
    """Test verify_json_content with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write("not valid json")
        tmp_path = tmp.name
    
    try:
        with patch('quickstart_validation.PROJECT_ROOT', Path(tmp_path).parent):
            file_name = Path(tmp_path).name
            result = verify_json_content(file_name)
            assert result is False
    finally:
        os.unlink(tmp_path)