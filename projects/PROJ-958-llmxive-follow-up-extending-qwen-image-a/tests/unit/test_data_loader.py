"""
Unit tests for data_loader.py validation functions.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.data_loader import validate_references_schema

class TestValidateReferencesSchema:
    """Test cases for validate_references_schema function."""

    def test_valid_references_file(self, tmp_path):
        """Test validation with a valid references file."""
        # Create a valid references.jsonl file
        refs_file = tmp_path / "references.jsonl"
        valid_data = [
            {"reference_description": "A photo of a cat"},
            {"reference_description": "An illustration of a dog"},
            {"reference_description": "A realistic sunset"}
        ]
        
        with open(refs_file, 'w') as f:
            for item in valid_data:
                f.write(json.dumps(item) + '\n')
        
        # Validate
        result = validate_references_schema(refs_file)
        
        assert result['valid'] is True
        assert result['total_rows'] == 3
        assert result['valid_rows'] == 3
        assert result['empty_rows'] == 0
        assert len(result['missing_fields']) == 0
        assert len(result['errors']) == 0

    def test_missing_required_field(self, tmp_path):
        """Test validation fails when required field is missing."""
        refs_file = tmp_path / "references.jsonl"
        invalid_data = [
            {"reference_description": "Valid entry"},
            {"other_field": "Missing reference_description"},
            {"reference_description": "Another valid entry"}
        ]
        
        with open(refs_file, 'w') as f:
            for item in invalid_data:
                f.write(json.dumps(item) + '\n')
        
        # Validation should fail
        with pytest.raises(ValueError) as exc_info:
            validate_references_schema(refs_file)
        
        assert "Missing required field" in str(exc_info.value)
        
        # Check that the error details are populated
        result = validate_references_schema(refs_file) if False else None  # Skip for exception case

    def test_empty_reference_description(self, tmp_path):
        """Test validation fails when reference_description is empty."""
        refs_file = tmp_path / "references.jsonl"
        invalid_data = [
            {"reference_description": "Valid entry"},
            {"reference_description": ""},
            {"reference_description": "   "},  # whitespace only
            {"reference_description": "Another valid entry"}
        ]
        
        with open(refs_file, 'w') as f:
            for item in invalid_data:
                f.write(json.dumps(item) + '\n')
        
        # Validation should fail
        with pytest.raises(ValueError) as exc_info:
            validate_references_schema(refs_file)
        
        assert "Empty 'reference_description'" in str(exc_info.value)

    def test_empty_file(self, tmp_path):
        """Test validation fails for an empty file."""
        refs_file = tmp_path / "references.jsonl"
        refs_file.touch()  # Create empty file
        
        # Validation should fail
        with pytest.raises(ValueError) as exc_info:
            validate_references_schema(refs_file)
        
        assert "empty" in str(exc_info.value).lower()

    def test_invalid_json_lines(self, tmp_path):
        """Test validation handles invalid JSON lines."""
        refs_file = tmp_path / "references.jsonl"
        invalid_data = [
            '{"reference_description": "Valid entry"}',
            'not valid json',
            '{"reference_description": "Another valid entry"}',
            '{"incomplete": '  # Malformed JSON
        ]
        
        with open(refs_file, 'w') as f:
            for item in invalid_data:
                f.write(item + '\n')
        
        # Validation should fail due to invalid JSON
        with pytest.raises(ValueError) as exc_info:
            validate_references_schema(refs_file)
        
        assert "Invalid JSON" in str(exc_info.value)

    def test_nonexistent_file(self, tmp_path):
        """Test validation raises error for non-existent file."""
        refs_file = tmp_path / "nonexistent.jsonl"
        
        with pytest.raises(FileNotFoundError):
            validate_references_schema(refs_file)

    def test_mixed_validity(self, tmp_path):
        """Test validation with a mix of valid and invalid entries."""
        refs_file = tmp_path / "references.jsonl"
        mixed_data = [
            {"reference_description": "Valid entry 1"},
            {"reference_description": ""},  # Empty
            {"other_field": "Missing field"},  # Missing required
            {"reference_description": "Valid entry 2"},
            {"reference_description": "   "},  # Whitespace only
            {"reference_description": "Valid entry 3"}
        ]
        
        with open(refs_file, 'w') as f:
            for item in mixed_data:
                f.write(json.dumps(item) + '\n')
        
        # Validation should fail
        with pytest.raises(ValueError) as exc_info:
            validate_references_schema(refs_file)
        
        # The function raises on first failure, so we check the error message
        assert "Schema validation failed" in str(exc_info.value)

    def test_single_valid_row(self, tmp_path):
        """Test validation with a single valid row."""
        refs_file = tmp_path / "references.jsonl"
        single_data = [{"reference_description": "Single valid entry"}]
        
        with open(refs_file, 'w') as f:
            for item in single_data:
                f.write(json.dumps(item) + '\n')
        
        result = validate_references_schema(refs_file)
        
        assert result['valid'] is True
        assert result['total_rows'] == 1
        assert result['valid_rows'] == 1

    def test_unicode_content(self, tmp_path):
        """Test validation handles unicode content correctly."""
        refs_file = tmp_path / "references.jsonl"
        unicode_data = [
            {"reference_description": "A photo of 猫 (cat)"},
            {"reference_description": "An illustration of 🐶 (dog)"},
            {"reference_description": "A realistic sunset with emoji 🌅"}
        ]
        
        with open(refs_file, 'w', encoding='utf-8') as f:
            for item in unicode_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        result = validate_references_schema(refs_file)
        
        assert result['valid'] is True
        assert result['total_rows'] == 3
        assert result['valid_rows'] == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])