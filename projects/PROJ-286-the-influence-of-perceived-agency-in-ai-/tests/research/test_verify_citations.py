import json
import os
import tempfile
import pytest
from code.research.verify_citations import verify_citations, main

def test_verify_all_valid():
    """Test that valid citations pass verification."""
    report = {
        "citations": [
            {"original": "Lee & See (2004)", "status": "valid", "overlap": 0.85},
            {"original": "Langer (1975)", "status": "valid", "overlap": 0.92}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report, f)
        temp_path = f.name

    try:
        assert verify_citations(temp_path) is True
    finally:
        os.unlink(temp_path)

def test_verify_invalid_status():
    """Test that invalid status raises error."""
    report = {
        "citations": [
            {"original": "Fake Citation (2099)", "status": "invalid", "overlap": 0.0}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Status is 'invalid'"):
            verify_citations(temp_path)
    finally:
        os.unlink(temp_path)

def test_verify_low_overlap():
    """Test that low overlap raises error."""
    report = {
        "citations": [
            {"original": "Lee & See (2004)", "status": "valid", "overlap": 0.5}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="below threshold"):
            verify_citations(temp_path)
    finally:
        os.unlink(temp_path)

def test_verify_missing_file():
    """Test that missing file raises error."""
    with pytest.raises(FileNotFoundError):
        verify_citations("nonexistent_file.json")

def test_verify_empty_citations():
    """Test that empty citations list raises error."""
    report = {"citations": []}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="No citations found"):
            verify_citations(temp_path)
    finally:
        os.unlink(temp_path)