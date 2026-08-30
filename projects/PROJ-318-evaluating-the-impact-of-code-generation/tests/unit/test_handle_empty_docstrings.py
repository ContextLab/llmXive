"""
Unit tests for T027: Handling empty/whitespace generated docstrings.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.handle_empty_docstrings import is_empty_or_whitespace, process_batch_file, GenerationException


class TestIsEmptyOrWhitespace(TestCase):
    def test_none(self):
        self.assertTrue(is_empty_or_whitespace(None))

    def test_empty_string(self):
        self.assertTrue(is_empty_or_whitespace(""))

    def test_whitespace_only(self):
        self.assertTrue(is_empty_or_whitespace("   "))
        self.assertTrue(is_empty_or_whitespace("\n\t"))

    def test_valid_string(self):
        self.assertFalse(is_empty_or_whitespace("Hello"))
        self.assertFalse(is_empty_or_whitespace(" Hello "))

    def test_non_string(self):
        self.assertFalse(is_empty_or_whitespace(123))
        self.assertFalse(is_empty_or_whitespace([]))


class TestProcessBatchFile(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_batch.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_docstring_sets_zero_and_review(self):
        data = [
            {
                "method_name": "test_func",
                "generated_docstring": "",
                "coverage_score": 0.5,
                "needs_review": False
            }
        ]
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        result = process_batch_file(self.test_file)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["coverage_score"], 0.0)
        self.assertTrue(result[0]["needs_review"])

    def test_whitespace_docstring_sets_zero_and_review(self):
        data = [
            {
                "method_name": "test_func",
                "generated_docstring": "   \n\t  ",
                "coverage_score": 0.8,
                "needs_review": False
            }
        ]
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        result = process_batch_file(self.test_file)

        self.assertEqual(result[0]["coverage_score"], 0.0)
        self.assertTrue(result[0]["needs_review"])

    def test_valid_docstring_resets_review_flag(self):
        data = [
            {
                "method_name": "test_func",
                "generated_docstring": "This is a valid docstring.",
                "coverage_score": 0.9,
                "needs_review": True
            }
        ]
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        result = process_batch_file(self.test_file)

        self.assertEqual(result[0]["coverage_score"], 0.9)
        self.assertFalse(result[0]["needs_review"])

    def test_missing_docstring_key_treated_as_empty(self):
        data = [
            {
                "method_name": "test_func",
                "coverage_score": 0.5,
                "needs_review": False
            }
        ]
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        result = process_batch_file(self.test_file)

        self.assertEqual(result[0]["coverage_score"], 0.0)
        self.assertTrue(result[0]["needs_review"])

    def test_none_docstring_treated_as_empty(self):
        data = [
            {
                "method_name": "test_func",
                "generated_docstring": None,
                "coverage_score": 0.5,
                "needs_review": False
            }
        ]
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        result = process_batch_file(self.test_file)

        self.assertEqual(result[0]["coverage_score"], 0.0)
        self.assertTrue(result[0]["needs_review"])

    def test_file_not_found_raises_exception(self):
        fake_path = Path(self.temp_dir) / "nonexistent.json"
        with self.assertRaises(GenerationException):
            process_batch_file(fake_path)

    def test_invalid_json_raises_exception(self):
        with open(self.test_file, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(GenerationException):
            process_batch_file(self.test_file)

    def test_non_list_data_raises_exception(self):
        with open(self.test_file, 'w') as f:
            json.dump({"key": "value"}, f)
        
        with self.assertRaises(GenerationException):
            process_batch_file(self.test_file)

    def test_mixed_records(self):
        data = [
            {"generated_docstring": "", "coverage_score": 0.5, "needs_review": False},
            {"generated_docstring": "Valid", "coverage_score": 0.5, "needs_review": True},
            {"generated_docstring": "   ", "coverage_score": 0.5, "needs_review": False},
            {"generated_docstring": "Also Valid", "coverage_score": 0.5, "needs_review": False},
        ]
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        result = process_batch_file(self.test_file)

        # Record 0: empty -> 0.0, True
        self.assertEqual(result[0]["coverage_score"], 0.0)
        self.assertTrue(result[0]["needs_review"])

        # Record 1: valid -> 0.5, False
        self.assertEqual(result[1]["coverage_score"], 0.5)
        self.assertFalse(result[1]["needs_review"])

        # Record 2: whitespace -> 0.0, True
        self.assertEqual(result[2]["coverage_score"], 0.0)
        self.assertTrue(result[2]["needs_review"])

        # Record 3: valid -> 0.5, False
        self.assertEqual(result[3]["coverage_score"], 0.5)
        self.assertFalse(result[3]["needs_review"])