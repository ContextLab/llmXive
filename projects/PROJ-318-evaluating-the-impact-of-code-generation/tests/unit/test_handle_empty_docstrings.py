"""
Unit tests for handle_empty_docstrings module.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.handle_empty_docstrings import (
    is_empty_or_whitespace,
    calculate_coverage_score_for_empty,
    process_batch_file,
    save_processed_batch,
    find_batch_files
)


class TestIsEmptyOrWhitespace:
    """Tests for is_empty_or_whitespace function"""
    
    def test_none_input(self):
        """Test that None returns True"""
        assert is_empty_or_whitespace(None) is True
    
    def test_empty_string(self):
        """Test that empty string returns True"""
        assert is_empty_or_whitespace("") is True
    
    def test_whitespace_only(self):
        """Test that whitespace-only string returns True"""
        assert is_empty_or_whitespace("   ") is True
        assert is_empty_or_whitespace("\t\n") is True
    
    def test_valid_docstring(self):
        """Test that valid docstring returns False"""
        assert is_empty_or_whitespace("This is a docstring") is False
        assert is_empty_or_whitespace("  Valid docstring  ") is False
    
    def test_non_string_input(self):
        """Test that non-string input returns True"""
        assert is_empty_or_whitespace(123) is True
        assert is_empty_or_whitespace([]) is True


class TestCalculateCoverageScoreForEmpty:
    """Tests for calculate_coverage_score_for_empty function"""
    
    def test_empty_params(self):
        """Test coverage with no AST params"""
        result = calculate_coverage_score_for_empty([])
        assert result == 0.0
    
    def test_with_params(self):
        """Test coverage with AST params (should still be 0.0)"""
        params = [
            {"name": "arg1", "type": "str"},
            {"name": "arg2", "type": "int"}
        ]
        result = calculate_coverage_score_for_empty(params)
        assert result == 0.0
    
    def test_formula_verification(self):
        """Test that the formula (0 / total) is correctly applied"""
        params = [{"name": f"arg{i}"} for i in range(5)]
        result = calculate_coverage_score_for_empty(params)
        # 0 matched / 5 total = 0.0
        assert result == 0.0


class TestProcessBatchFile:
    """Tests for process_batch_file function"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_process_with_empty_docstrings(self, temp_dir):
        """Test processing records with empty docstrings"""
        # Create test data
        test_data = [
            {
                "method_name": "test_method1",
                "generated_docstring": "",
                "ast_params": [{"name": "arg1"}],
                "original_docstring": "Original docstring"
            },
            {
                "method_name": "test_method2",
                "generated_docstring": "   ",
                "ast_params": [{"name": "arg2"}],
                "original_docstring": "Another docstring"
            },
            {
                "method_name": "test_method3",
                "generated_docstring": "Valid docstring",
                "ast_params": [{"name": "arg3"}],
                "original_docstring": "Original docstring"
            }
        ]
        
        input_file = temp_dir / "test_batch.json"
        with open(input_file, 'w') as f:
            json.dump(test_data, f)
        
        # Process the file
        result = process_batch_file(input_file)
        
        # Verify results
        assert len(result) == 3
        
        # First record: empty docstring
        assert result[0]["needs_review"] is True
        assert result[0]["coverage_score"] == 0.0
        
        # Second record: whitespace docstring
        assert result[1]["needs_review"] is True
        assert result[1]["coverage_score"] == 0.0
        
        # Third record: valid docstring
        assert result[2].get("needs_review", False) is False
        assert "coverage_score" not in result[2]  # Not calculated for non-empty
    
    def test_process_missing_file(self, temp_dir):
        """Test processing a non-existent file"""
        with pytest.raises(FileNotFoundError):
            process_batch_file(temp_dir / "nonexistent.json")


class TestSaveProcessedBatch:
    """Tests for save_processed_batch function"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_save_records(self, temp_dir):
        """Test saving records to file"""
        test_records = [
            {"method_name": "test1", "needs_review": True},
            {"method_name": "test2", "needs_review": False}
        ]
        
        output_file = temp_dir / "output.json"
        save_processed_batch(test_records, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 2
        assert saved_data[0]["method_name"] == "test1"
        assert saved_data[1]["method_name"] == "test2"
    
    def test_create_parent_directories(self, temp_dir):
        """Test that parent directories are created"""
        test_records = [{"method_name": "test"}]
        output_file = temp_dir / "subdir" / "nested" / "output.json"
        
        save_processed_batch(test_records, output_file)
        
        assert output_file.exists()


class TestFindBatchFiles:
    """Tests for find_batch_files function"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_find_batch_files(self, temp_dir):
        """Test finding batch files"""
        # Create test files
        (temp_dir / "generation_batch_repo1.json").touch()
        (temp_dir / "generation_batch_repo2.json").touch()
        (temp_dir / "generation_batch_repo1_cleaned.json").touch()  # Should be excluded
        (temp_dir / "other_file.json").touch()  # Should be excluded
        
        batch_files = find_batch_files(temp_dir)
        
        assert len(batch_files) == 2
        names = [f.name for f in batch_files]
        assert "generation_batch_repo1.json" in names
        assert "generation_batch_repo2.json" in names
        assert "generation_batch_repo1_cleaned.json" not in names
    
    def test_no_batch_files(self, temp_dir):
        """Test when no batch files exist"""
        batch_files = find_batch_files(temp_dir)
        assert len(batch_files) == 0