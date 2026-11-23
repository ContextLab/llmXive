"""
Tests for code/research/verify_citations.py
"""
import json
import os
import tempfile
import pytest
from code.research.verify_citations import verify_citations, main
import sys
from io import StringIO

def test_verify_valid_citations():
    """Test that valid citations pass verification."""
    valid_data = {
        "citations": [
            {"citation": "Lee & See (2004)", "status": "valid", "overlap": 0.85},
            {"citation": "Langer (1975)", "status": "valid", "overlap": 0.72}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_data, f)
        temp_path = f.name

    try:
        result = verify_citations(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_verify_invalid_status():
    """Test that citations with invalid status fail."""
    invalid_data = {
        "citations": [
            {"citation": "Fake Citation", "status": "invalid", "overlap": 0.90}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            verify_citations(temp_path)
        assert "Invalid status" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

def test_verify_low_overlap():
    """Test that citations with low overlap fail."""
    invalid_data = {
        "citations": [
            {"citation": "Weak Match", "status": "valid", "overlap": 0.50}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            verify_citations(temp_path)
        assert "low overlap" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

def test_verify_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        verify_citations("non_existent_file.json")

def test_verify_empty_citations():
    """Test that empty citations list raises ValueError."""
    empty_data = {"citations": []}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(empty_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            verify_citations(temp_path)
        assert "No citations found" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

def test_main_success(capfd):
    """Test main function with valid data."""
    valid_data = {
        "citations": [
            {"citation": "Test", "status": "valid", "overlap": 0.8}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_data, f)
        temp_path = f.name

    try:
        sys.argv = ['verify_citations.py', temp_path]
        main()
        captured = capfd.readouterr()
        assert "SUCCESS" in captured.out
    finally:
        os.unlink(temp_path)

def test_main_failure(capfd):
    """Test main function with invalid data."""
    invalid_data = {
        "citations": [
            {"citation": "Bad", "status": "invalid", "overlap": 0.9}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_data, f)
        temp_path = f.name

    try:
        sys.argv = ['verify_citations.py', temp_path]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capfd.readouterr()
        assert "VERIFICATION FAILED" in captured.err
    finally:
        os.unlink(temp_path)
