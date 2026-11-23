"""
Unit tests for the post-processing script (T027).
Tests handling of empty/whitespace generated docstrings.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.post_process import (
    is_empty_or_whitespace,
    find_batch_files,
    process_batch_file,
    save_processed_batch
)

class TestIsEmptyOrWhitespace:
    """Tests for the is_empty_or_whitespace helper function."""

    def test_none_input(self):
        """Test that None is considered empty."""
        assert is_empty_or_whitespace(None) is True

    def test_empty_string(self):
        """Test that empty string is considered empty."""
        assert is_empty_or_whitespace("") is True

    def test_whitespace_only(self):
        """Test that whitespace-only strings are considered empty."""
        assert is_empty_or_whitespace("   ") is True
        assert is_empty_or_whitespace("\t\n") is True
        assert is_empty_or_whitespace("  \t  \n  ") is True

    def test_valid_docstring(self):
        """Test that valid docstrings are not considered empty."""
        assert is_empty_or_whitespace("This is a docstring") is False
        assert is_empty_or_whitespace("  Leading space") is False
        assert is_empty_or_whitespace("Trailing space  ") is False
        assert is_empty_or_whitespace("  Both  ") is False

    def test_non_string_type(self):
        """Test that non-string types are handled gracefully (return True)."""
        assert is_empty_or_whitespace(123) is True
        assert is_empty_or_whitespace([]) is True
        assert is_empty_or_whitespace({}) is True

class TestFindBatchFiles:
    """Tests for the find_batch_files function."""

    def test_no_batch_files(self, tmp_path):
        """Test behavior when no batch files exist."""
        batch_files = find_batch_files(tmp_path)
        assert batch_files == []

    def test_single_batch_file(self, tmp_path):
        """Test finding a single batch file."""
        test_file = tmp_path / "generation_batch_repo1.json"
        test_file.write_text("[]")
        
        batch_files = find_batch_files(tmp_path)
        assert len(batch_files) == 1
        assert batch_files[0].name == "generation_batch_repo1.json"

    def test_multiple_batch_files_sorted(self, tmp_path):
        """Test that multiple batch files are returned in sorted order."""
        files = [
            "generation_batch_z.json",
            "generation_batch_a.json",
            "generation_batch_m.json"
        ]
        for fname in files:
            (tmp_path / fname).write_text("[]")
        
        batch_files = find_batch_files(tmp_path)
        assert len(batch_files) == 3
        # Should be sorted alphabetically
        assert [f.name for f in batch_files] == [
            "generation_batch_a.json",
            "generation_batch_m.json",
            "generation_batch_z.json"
        ]

    def test_excludes_cleaned_files(self, tmp_path):
        """Test that cleaned files are excluded from the list."""
        (tmp_path / "generation_batch_a.json").write_text("[]")
        (tmp_path / "generation_batch_a_cleaned.json").write_text("[]")
        
        batch_files = find_batch_files(tmp_path)
        assert len(batch_files) == 1
        assert batch_files[0].name == "generation_batch_a.json"

class TestProcessBatchFile:
    """Tests for the process_batch_file function."""

    def test_empty_batch_file(self, tmp_path):
        """Test processing an empty batch file."""
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text("[]")
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        stats = process_batch_file(input_file, output_file)
        
        assert stats['total_records'] == 0
        assert stats['processed_records'] == 0
        assert stats['flagged_records'] == 0
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        assert result == []

    def test_batch_with_no_docstrings(self, tmp_path):
        """Test processing a batch where all docstrings are missing/empty."""
        records = [
            {"method_name": "m1", "generated_docstring": None},
            {"method_name": "m2", "generated_docstring": ""},
            {"method_name": "m3", "generated_docstring": "   "}
        ]
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text(json.dumps(records))
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        stats = process_batch_file(input_file, output_file)
        
        assert stats['total_records'] == 3
        assert stats['flagged_records'] == 3
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        for rec in result:
            assert rec['needs_review'] is True

    def test_batch_with_valid_docstrings(self, tmp_path):
        """Test processing a batch with all valid docstrings."""
        records = [
            {"method_name": "m1", "generated_docstring": "Valid docstring 1"},
            {"method_name": "m2", "generated_docstring": "Valid docstring 2"}
        ]
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text(json.dumps(records))
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        stats = process_batch_file(input_file, output_file)
        
        assert stats['total_records'] == 2
        assert stats['flagged_records'] == 0
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        for rec in result:
            assert rec['needs_review'] is False

    def test_batch_mixed_docstrings(self, tmp_path):
        """Test processing a batch with mixed valid and empty docstrings."""
        records = [
            {"method_name": "m1", "generated_docstring": "Valid"},
            {"method_name": "m2", "generated_docstring": None},
            {"method_name": "m3", "generated_docstring": "Also valid"},
            {"method_name": "m4", "generated_docstring": ""}
        ]
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text(json.dumps(records))
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        stats = process_batch_file(input_file, output_file)
        
        assert stats['total_records'] == 4
        assert stats['flagged_records'] == 2  # m2 and m4
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert result[0]['needs_review'] is False
        assert result[1]['needs_review'] is True
        assert result[2]['needs_review'] is False
        assert result[3]['needs_review'] is True

    def test_preserves_other_fields(self, tmp_path):
        """Test that non-docstring fields are preserved."""
        records = [
            {
                "method_name": "m1",
                "generated_docstring": "",
                "ast_params": ["x", "y"],
                "source_file": "test.py",
                "line_number": 10,
                "custom_field": "preserved"
            }
        ]
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text(json.dumps(records))
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        process_batch_file(input_file, output_file)
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert result[0]['ast_params'] == ["x", "y"]
        assert result[0]['source_file'] == "test.py"
        assert result[0]['line_number'] == 10
        assert result[0]['custom_field'] == "preserved"

    def test_missing_file_raises_error(self, tmp_path):
        """Test that processing a non-existent file raises FileNotFoundError."""
        input_file = tmp_path / "nonexistent.json"
        output_file = tmp_path / "output.json"
        
        with pytest.raises(FileNotFoundError):
            process_batch_file(input_file, output_file)

    def test_invalid_json_raises_error(self, tmp_path):
        """Test that processing invalid JSON raises an error."""
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text("not valid json")
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        with pytest.raises(json.JSONDecodeError):
            process_batch_file(input_file, output_file)

    def test_non_list_json_raises_error(self, tmp_path):
        """Test that processing non-list JSON raises ValueError."""
        input_file = tmp_path / "generation_batch_test.json"
        input_file.write_text('{"key": "value"}')
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        
        with pytest.raises(ValueError):
            process_batch_file(input_file, output_file)

class TestSaveProcessedBatch:
    """Tests for the save_processed_batch function."""

    def test_saves_stats_file(self, tmp_path):
        """Test that stats are saved correctly."""
        output_file = tmp_path / "generation_batch_test_cleaned.json"
        output_file.write_text("[]")
        
        stats = {
            'input_file': 'test.json',
            'output_file': 'test_cleaned.json',
            'total_records': 10,
            'processed_records': 10,
            'flagged_records': 2,
            'flagged_percentage': 20.0
        }
        
        save_processed_batch(output_file, stats)
        
        stats_file = tmp_path / "generation_batch_test_cleaned_stats.json"
        assert stats_file.exists()
        
        with open(stats_file, 'r') as f:
            saved_stats = json.load(f)
        
        assert saved_stats == stats