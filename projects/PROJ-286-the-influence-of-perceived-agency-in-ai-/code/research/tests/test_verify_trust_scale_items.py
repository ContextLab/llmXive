"""
Unit tests for T011: verify_trust_scale_items.py
"""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.research.verify_trust_scale_items import (
    load_trust_scale_items,
    load_validation_report,
    verify_items,
    PRIMARY_SOURCE_TRUTH
)

class TestLoadTrustScaleItems:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON array of scale items."""
        valid_items = ["Item 1", "Item 2", "Item 3"]
        scale_file = tmp_path / "scale_items.md"
        with open(scale_file, 'w') as f:
            json.dump(valid_items, f)
        
        loaded = load_trust_scale_items(scale_file)
        assert loaded == valid_items

    def test_load_nonexistent_file(self, tmp_path):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_trust_scale_items(tmp_path / "nonexistent.json")

    def test_load_invalid_json(self, tmp_path):
        """Test that loading invalid JSON raises ValueError."""
        scale_file = tmp_path / "invalid.json"
        scale_file.write_text("not valid json")
        
        with pytest.raises(ValueError):
            load_trust_scale_items(scale_file)

    def test_load_non_array_json(self, tmp_path):
        """Test that loading a non-array JSON raises ValueError."""
        scale_file = tmp_path / "non_array.json"
        with open(scale_file, 'w') as f:
            json.dump({"key": "value"}, f)
        
        with pytest.raises(ValueError):
            load_trust_scale_items(scale_file)

class TestLoadValidationReport:
    def test_load_valid_report(self, tmp_path):
        """Test loading a valid validation report."""
        report = {"status": "verified", "items_verified": 12}
        report_file = tmp_path / "report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f)
        
        loaded = load_validation_report(report_file)
        assert loaded == report

    def test_load_nonexistent_report(self, tmp_path):
        """Test that loading a nonexistent report raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_validation_report(tmp_path / "nonexistent.json")

class TestVerifyItems:
    def test_exact_match(self):
        """Test that identical lists return True with no mismatches."""
        is_valid, mismatches = verify_items(PRIMARY_SOURCE_TRUTH, PRIMARY_SOURCE_TRUTH)
        assert is_valid is True
        assert len(mismatches) == 0

    def test_length_mismatch(self):
        """Test that different lengths are detected."""
        short_list = PRIMARY_SOURCE_TRUTH[:5]
        is_valid, mismatches = verify_items(short_list, PRIMARY_SOURCE_TRUTH)
        assert is_valid is False
        assert "Length mismatch" in mismatches[0]

    def test_content_mismatch(self):
        """Test that content differences are detected."""
        modified_list = PRIMARY_SOURCE_TRUTH.copy()
        modified_list[0] = "Modified item"
        
        is_valid, mismatches = verify_items(modified_list, PRIMARY_SOURCE_TRUTH)
        assert is_valid is False
        assert any("Item 1 mismatch" in msg for msg in mismatches)

    def test_empty_lists(self):
        """Test that empty lists match."""
        is_valid, mismatches = verify_items([], [])
        assert is_valid is True
        assert len(mismatches) == 0

class TestPrimarySourceTruth:
    def test_has_correct_length(self):
        """Test that the primary source truth has 12 items."""
        assert len(PRIMARY_SOURCE_TRUTH) == 12

    def test_contains_expected_items(self):
        """Test that the primary source truth contains expected key phrases."""
        expected_phrases = [
            "predictable",
            "consistent",
            "reliable",
            "accurate",
            "trustworthy",
            "safe",
            "effective",
            "competent",
            "helpful",
            "honest",
            "benevolent",
            "open"
        ]
        
        for phrase in expected_phrases:
            found = any(phrase.lower() in item.lower() for item in PRIMARY_SOURCE_TRUTH)
            assert found, f"Expected phrase '{phrase}' not found in primary source truth"

def test_verify_items_with_whitespace():
    """Test that whitespace differences are detected (exact match required)."""
    list_with_extra_space = PRIMARY_SOURCE_TRUTH.copy()
    list_with_extra_space[0] = PRIMARY_SOURCE_TRUTH[0] + " "  # Extra space at end
    
    is_valid, mismatches = verify_items(list_with_extra_space, PRIMARY_SOURCE_TRUTH)
    assert is_valid is False
    assert any("Item 1 mismatch" in msg for msg in mismatches)
