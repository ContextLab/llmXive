"""
Unit tests for test_transformer.py
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from test_transformer import (
    sanitize_filename,
    extract_test_code,
    transform_test_suite,
    save_test_file,
    process_catalog_entry,
    run_transformation
)

class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_task_id(self):
        """Test with a simple task ID."""
        assert sanitize_filename("1") == "1"
        assert sanitize_filename("task_1") == "task_1"

    def test_human_eval_format(self):
        """Test with HumanEval format (contains slash)."""
        assert sanitize_filename("HumanEval/0") == "HumanEval__0"
        assert sanitize_filename("HumanEval/123") == "HumanEval__123"

    def test_mbpp_format(self):
        """Test with MBPP format."""
        assert sanitize_filename("MBPP/42") == "MBPP__42"

    def test_special_characters(self):
        """Test removal of special characters."""
        assert sanitize_filename("task@123#test") == "task_123_test"
        assert sanitize_filename("file<with>special|chars") == "file_with_special_chars"

    def test_underscore_preservation(self):
        """Test that underscores are preserved."""
        assert sanitize_filename("my_task_id") == "my_task_id"

class TestExtractTestCode:
    """Tests for extract_test_code function."""

    def test_plain_code(self):
        """Test extraction of plain code."""
        code = "def test_example():\n    assert 1 + 1 == 2"
        assert extract_test_code(code) == code

    def test_markdown_python_block(self):
        """Test extraction from markdown python block."""
        code = "```python\ndef test_example():\n    assert 1 + 1 == 2\n```"
        expected = "def test_example():\n    assert 1 + 1 == 2"
        assert extract_test_code(code) == expected

    def test_markdown_block_no_language(self):
        """Test extraction from markdown block without language."""
        code = "```\ndef test_example():\n    assert 1 + 1 == 2\n```"
        expected = "def test_example():\n    assert 1 + 1 == 2"
        assert extract_test_code(code) == expected

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is removed."""
        code = "   def test_example():\n    assert 1 + 1 == 2   "
        expected = "def test_example():\n    assert 1 + 1 == 2"
        assert extract_test_code(code) == expected

    def test_empty_input(self):
        """Test handling of empty input."""
        assert extract_test_code("") == ""
        assert extract_test_code(None) == ""

    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert extract_test_code(123) == ""
        assert extract_test_code([]) == ""

class TestTransformTestSuite:
    """Tests for transform_test_suite function."""

    def test_basic_transformation(self):
        """Test basic transformation of a test suite."""
        test_string = "def test_example():\n    assert 1 + 1 == 2"
        result = transform_test_suite("task_1", test_string, "mbpp")
        
        assert result is not None
        assert "# Auto-generated test file for mbpp/task_1" in result
        assert "def test_example()" in result
        assert "assert 1 + 1 == 2" in result

    def test_empty_test_suite(self):
        """Test handling of empty test suite."""
        result = transform_test_suite("task_1", "", "mbpp")
        assert result is None

    def test_none_test_suite(self):
        """Test handling of None test suite."""
        result = transform_test_suite("task_1", None, "mbpp")
        assert result is None

    def test_markdown_wrapped_code(self):
        """Test transformation of markdown-wrapped code."""
        test_string = "```python\ndef test_example():\n    assert True\n```"
        result = transform_test_suite("task_2", test_string, "humaneval")
        
        assert result is not None
        assert "# Auto-generated test file for humaneval/task_2" in result
        assert "def test_example()" in result

    def test_whitespace_in_test_suite(self):
        """Test transformation with whitespace in test suite."""
        test_string = "   def test_example():\n    assert True   "
        result = transform_test_suite("task_3", test_string, "mbpp")
        
        assert result is not None
        # The function should strip whitespace from the code
        assert "def test_example()" in result

class TestSaveTestFile:
    """Tests for save_test_file function."""

    def test_save_file(self, tmp_path):
        """Test saving a test file."""
        # Create a temporary directory for testing
        with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path)):
            test_code = "def test_example():\n    assert True"
            filepath = save_test_file("task_1", test_code, "mbpp")
            
            assert os.path.exists(filepath)
            assert filepath.endswith("task_1.py")
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "def test_example()" in content
                assert "assert True" in content

    def test_sanitize_filename_in_path(self, tmp_path):
        """Test that filename is sanitized in the path."""
        with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path)):
            test_code = "def test_example():\n    assert True"
            filepath = save_test_file("HumanEval/1", test_code, "humaneval")
            
            assert os.path.exists(filepath)
            assert "HumanEval__1.py" in filepath

class TestProcessCatalogEntry:
    """Tests for process_catalog_entry function."""

    def test_valid_entry(self, tmp_path):
        """Test processing a valid catalog entry."""
        entry = {
            "task_id": "task_1",
            "test_suite": "def test_example():\n    assert True",
            "dataset_source": "mbpp"
        }
        
        with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path)):
            result = process_catalog_entry(entry)
            assert result is True

    def test_missing_task_id(self, tmp_path):
        """Test processing an entry with missing task_id."""
        entry = {
            "test_suite": "def test_example():\n    assert True"
        }
        
        with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path)):
            result = process_catalog_entry(entry)
            assert result is False

    def test_missing_test_suite(self, tmp_path):
        """Test processing an entry with missing test_suite."""
        entry = {
            "task_id": "task_1"
        }
        
        with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path)):
            result = process_catalog_entry(entry)
            assert result is False

    def test_invalid_test_suite_format(self, tmp_path):
        """Test processing an entry with invalid test suite format."""
        entry = {
            "task_id": "task_1",
            "test_suite": None
        }
        
        with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path)):
            result = process_catalog_entry(entry)
            assert result is False

class TestRunTransformation:
    """Tests for run_transformation function."""

    def test_missing_catalog(self):
        """Test when catalog file is missing."""
        with patch('test_transformer.CATALOG_PATH', '/nonexistent/path/catalog.json'):
            result = run_transformation()
            assert result is False

    def test_empty_catalog(self, tmp_path):
        """Test with an empty catalog."""
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps({"tasks": []}))
        
        with patch('test_transformer.CATALOG_PATH', str(catalog_path)):
            with patch('test_transformer.TESTS_OUTPUT_DIR', str(tmp_path / "tests")):
                result = run_transformation()
                assert result is True  # No failures, just no tasks

    def test_successful_transformation(self, tmp_path):
        """Test successful transformation of multiple tasks."""
        catalog_path = tmp_path / "catalog.json"
        catalog_data = {
            "tasks": [
                {
                    "task_id": "task_1",
                    "test_suite": "def test_1():\n    assert True",
                    "dataset_source": "mbpp"
                },
                {
                    "task_id": "HumanEval/2",
                    "test_suite": "def test_2():\n    assert False",
                    "dataset_source": "humaneval"
                }
            ]
        }
        catalog_path.write_text(json.dumps(catalog_data))
        
        tests_dir = tmp_path / "tests"
        
        with patch('test_transformer.CATALOG_PATH', str(catalog_path)):
            with patch('test_transformer.TESTS_OUTPUT_DIR', str(tests_dir)):
                result = run_transformation()
                
                assert result is True
                assert (tests_dir / "task_1.py").exists()
                assert (tests_dir / "HumanEval__2.py").exists()

    def test_skipped_tasks(self, tmp_path):
        """Test skipping tasks with missing test suites."""
        catalog_path = tmp_path / "catalog.json"
        catalog_data = {
            "tasks": [
                {
                    "task_id": "task_1",
                    "test_suite": "def test_1():\n    assert True",
                    "dataset_source": "mbpp"
                },
                {
                    "task_id": "task_2",
                    # Missing test_suite
                    "dataset_source": "mbpp"
                }
            ]
        }
        catalog_path.write_text(json.dumps(catalog_data))
        
        tests_dir = tmp_path / "tests"
        
        with patch('test_transformer.CATALOG_PATH', str(catalog_path)):
            with patch('test_transformer.TESTS_OUTPUT_DIR', str(tests_dir)):
                result = run_transformation()
                
                # Should succeed (no failures, just skips)
                assert result is True
                assert (tests_dir / "task_1.py").exists()
                assert not (tests_dir / "task_2.py").exists()