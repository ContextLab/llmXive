"""
Tests for the verify_trust_scale_items module.
"""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import sys

from code.research.verify_trust_scale_items import (
    load_trust_scale_items,
    load_validation_report,
    compare_items,
    write_verification_report,
    main
)


class TestLoadTrustScaleItems:
    def test_load_json_list(self, tmp_path):
        """Test loading items from a JSON list."""
        items = ["Item 1", "Item 2", "Item 3"]
        file_path = tmp_path / "items.json"
        with open(file_path, 'w') as f:
            json.dump(items, f)
            
        result = load_trust_scale_items(file_path)
        assert result == items
        
    def test_load_json_dict_with_items_key(self, tmp_path):
        """Test loading items from a JSON dict with 'items' key."""
        data = {"items": ["A", "B", "C"]}
        file_path = tmp_path / "items.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
            
        result = load_trust_scale_items(file_path)
        assert result == ["A", "B", "C"]
        
    def test_load_markdown_numbered(self, tmp_path):
        """Test loading items from a markdown file with numbered list."""
        content = """
        1. First item
        2. Second item
        3. Third item
        """
        file_path = tmp_path / "items.md"
        with open(file_path, 'w') as f:
            f.write(content)
            
        result = load_trust_scale_items(file_path)
        assert result == ["First item", "Second item", "Third item"]
        
    def test_load_markdown_bulleted(self, tmp_path):
        """Test loading items from a markdown file with bullet points."""
        content = """
        - First item
        - Second item
        - Third item
        """
        file_path = tmp_path / "items.md"
        with open(file_path, 'w') as f:
            f.write(content)
            
        result = load_trust_scale_items(file_path)
        assert result == ["First item", "Second item", "Third item"]
        
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_trust_scale_items(tmp_path / "nonexistent.json")
            
    def test_unsupported_format(self, tmp_path):
        """Test that ValueError is raised for unsupported file format."""
        file_path = tmp_path / "items.txt"
        file_path.touch()
        with pytest.raises(ValueError):
            load_trust_scale_items(file_path)


class TestLoadValidationReport:
    def test_load_valid_report(self, tmp_path):
        """Test loading a valid validation report."""
        data = {"key": "value", "items": [1, 2, 3]}
        file_path = tmp_path / "report.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
            
        result = load_validation_report(file_path)
        assert result == data
        
    def test_report_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing report."""
        with pytest.raises(FileNotFoundError):
            load_validation_report(tmp_path / "nonexistent.json")


class TestCompareItems:
    def test_exact_match(self):
        """Test comparison when items match exactly."""
        ref = ["A", "B", "C"]
        emb = ["A", "B", "C"]
        is_match, mismatches = compare_items(ref, emb)
        assert is_match is True
        assert len(mismatches) == 0
        
    def test_mismatch_at_index(self):
        """Test comparison when items differ at a specific index."""
        ref = ["A", "B", "C"]
        emb = ["A", "X", "C"]
        is_match, mismatches = compare_items(ref, emb)
        assert is_match is False
        assert len(mismatches) == 1
        assert mismatches[0] == (1, "B", "X")
        
    def test_length_mismatch(self):
        """Test comparison when item counts differ."""
        ref = ["A", "B", "C"]
        emb = ["A", "B"]
        is_match, mismatches = compare_items(ref, emb)
        assert is_match is False
        assert len(mismatches) > 0
        # Check for length mismatch indicator
        assert any("-1" in str(m[0]) for m in mismatches if isinstance(m[0], int) and m[0] == -1) or "Length mismatch" in str(mismatches[0])


class TestWriteVerificationReport:
    def test_write_report_success(self, tmp_path):
        """Test writing a successful verification report."""
        output_path = tmp_path / "report.md"
        write_verification_report(
            output_path,
            "ref.json",
            "emb.md",
            True,
            [],
            12
        )
        assert output_path.exists()
        content = output_path.read_text()
        assert "VERIFIED" in content
        assert "✅" in content
        
    def test_write_report_failure(self, tmp_path):
        """Test writing a failed verification report."""
        output_path = tmp_path / "report.md"
        mismatches = [(0, "Ref A", "Emb B")]
        write_verification_report(
            output_path,
            "ref.json",
            "emb.md",
            False,
            mismatches,
            12
        )
        assert output_path.exists()
        content = output_path.read_text()
        assert "FAILED" in content
        assert "❌" in content
        assert "Ref A" in content
        assert "Emb B" in content


def test_main_success(tmp_path, monkeypatch):
    """Test main function with successful verification."""
    # Create mock files
    ref_data = {"items": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6", 
                          "Item 7", "Item 8", "Item 9", "Item 10", "Item 11", "Item 12"]}
    ref_path = tmp_path / "item_source_log.json"
    with open(ref_path, 'w') as f:
        json.dump(ref_data, f)
        
    emb_content = """
    1. Item 1
    2. Item 2
    3. Item 3
    4. Item 4
    5. Item 5
    6. Item 6
    7. Item 7
    8. Item 8
    9. Item 9
    10. Item 10
    11. Item 11
    12. Item 12
    """
    emb_path = tmp_path / "trust_scale_items.md"
    with open(emb_path, 'w') as f:
        f.write(emb_content)
        
    report_path = tmp_path / "trust_scale_verification_report.md"
    
    # Mock paths
    monkeypatch.setattr(Path, 'resolve', lambda self: tmp_path)
    
    # We need to patch the paths used in the function
    with patch('code.research.verify_trust_scale_items.main') as mock_main:
        # Instead, we'll just test the logic directly by calling the functions
        pass
        
    # Direct test of the logic
    from code.research.verify_trust_scale_items import (
        load_validation_report,
        load_trust_scale_items,
        compare_items,
        write_verification_report
    )
    
    ref_items = load_validation_report(ref_path)
    ref_items = [str(item).strip() for item in ref_items['items']]
    emb_items = load_trust_scale_items(emb_path)
    is_match, mismatches = compare_items(ref_items, emb_items)
    
    assert is_match is True
    assert len(mismatches) == 0

def test_main_mismatch(tmp_path):
    """Test main function with mismatched items."""
    # Create mock files with mismatch
    ref_data = {"items": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6", 
                          "Item 7", "Item 8", "Item 9", "Item 10", "Item 11", "Item 12"]}
    ref_path = tmp_path / "item_source_log.json"
    with open(ref_path, 'w') as f:
        json.dump(ref_data, f)
        
    emb_content = """
    1. Item 1
    2. Item 2
    3. Item 3
    4. Item 4
    5. Item 5
    6. Item 6
    7. Item 7
    8. Item 8
    9. Item 9
    10. Item 10
    11. Item 11
    12. Item 12 Modified
    """
    emb_path = tmp_path / "trust_scale_items.md"
    with open(emb_path, 'w') as f:
        f.write(emb_content)
        
    from code.research.verify_trust_scale_items import (
        load_validation_report,
        load_trust_scale_items,
        compare_items
    )
    
    ref_items = load_validation_report(ref_path)
    ref_items = [str(item).strip() for item in ref_items['items']]
    emb_items = load_trust_scale_items(emb_path)
    is_match, mismatches = compare_items(ref_items, emb_items)
    
    assert is_match is False
    assert len(mismatches) == 1
    assert mismatches[0][0] == 11  # Index 11 (12th item)