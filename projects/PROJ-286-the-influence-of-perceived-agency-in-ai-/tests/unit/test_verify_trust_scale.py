"""
Unit tests for the trust scale verification script.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from research.verify_trust_scale import (
    load_trust_scale_items,
    load_validation_report,
    verify_items,
    EXPECTED_ITEMS
)

def test_load_trust_scale_items_valid():
    """Test loading valid trust scale items from markdown file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Trust Scale\n\n```json\n")
        f.write(json.dumps(EXPECTED_ITEMS))
        f.write("\n```\n")
        f_path = Path(f.name)
    
    try:
        items = load_trust_scale_items(f_path)
        assert len(items) == len(EXPECTED_ITEMS)
        assert items == EXPECTED_ITEMS
    finally:
        f_path.unlink()

def test_load_trust_scale_items_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_trust_scale_items(Path("nonexistent_file.md"))

def test_load_trust_scale_items_invalid_json():
    """Test that invalid JSON raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Trust Scale\n\n```json\n")
        f.write("invalid json")
        f.write("\n```\n")
        f_path = Path(f.name)
    
    try:
        with pytest.raises(json.JSONDecodeError):
            load_trust_scale_items(f_path)
    finally:
        f_path.unlink()

def test_load_validation_report_valid():
    """Test loading valid validation report."""
    report_data = [
        {"title": "Lee & See (2004)", "doi": "10.1518/001872004772976155", "status": "valid"},
        {"title": "Langer (1975)", "doi": "10.1037/0022-3514.31.5.792", "status": "valid"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report_data, f)
        f_path = Path(f.name)
    
    try:
        report = load_validation_report(f_path)
        assert len(report) == 2
        assert report[0]["status"] == "valid"
    finally:
        f_path.unlink()

def test_verify_items_success():
    """Test successful verification of items."""
    validation_report = [
        {"title": "Lee & See (2004)", "status": "valid"}
    ]
    
    is_verified, message = verify_items(EXPECTED_ITEMS, validation_report)
    
    assert is_verified is True
    assert "successfully" in message.lower()

def test_verify_items_count_mismatch():
    """Test verification failure due to item count mismatch."""
    validation_report = [
        {"title": "Lee & See (2004)", "status": "valid"}
    ]
    
    short_items = EXPECTED_ITEMS[:5]
    is_verified, message = verify_items(short_items, validation_report)
    
    assert is_verified is False
    assert "count mismatch" in message.lower()

def test_verify_items_content_mismatch():
    """Test verification failure due to content mismatch."""
    validation_report = [
        {"title": "Lee & See (2004)", "status": "valid"}
    ]
    
    mismatched_items = EXPECTED_ITEMS.copy()
    mismatched_items[0] = "I do not trust this system"
    
    is_verified, message = verify_items(mismatched_items, validation_report)
    
    assert is_verified is False
    assert "mismatch" in message.lower()

def test_verify_items_invalid_citation():
    """Test verification failure due to invalid citation status."""
    validation_report = [
        {"title": "Lee & See (2004)", "status": "invalid"}
    ]
    
    is_verified, message = verify_items(EXPECTED_ITEMS, validation_report)
    
    assert is_verified is False
    assert "no valid citations" in message.lower()