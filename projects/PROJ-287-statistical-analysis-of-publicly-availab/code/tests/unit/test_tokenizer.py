"""
Unit tests for the tokenizer module.
"""
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.preprocess.tokenizer import (
    TokenizationResult,
    WindowStopwordLoader,
    AbstractTokenizer,
    load_preprocessed_data,
    save_tokenized_results
)


class TestTokenizationResult(unittest.TestCase):
    """Tests for the TokenizationResult dataclass."""
    
    def test_creation(self):
        """Test that TokenizationResult can be created with all fields."""
        result = TokenizationResult(
            original_text="Test abstract",
            tokens=["test", "abstract"],
            tokens_lower=["test", "abstract"],
            tokens_stopped=["test", "abstract"],
            window="2000-2004",
            record_id="test-001",
            token_count=2,
            stopped_count=2
        )
        
        self.assertEqual(result.record_id, "test-001")
        self.assertEqual(result.window, "2000-2004")
        self.assertEqual(result.token_count, 2)
        self.assertEqual(result.stopped_count, 2)
    
    def test_fields_are_correct_types(self):
        """Test that all fields have correct types."""
        result = TokenizationResult(
            original_text="Test",
            tokens=[],
            tokens_lower=[],
            tokens_stopped=[],
            window="2000-2004",
            record_id="test-001",
            token_count=0,
            stopped_count=0
        )
        
        self.assertIsInstance(result.original_text, str)
        self.assertIsInstance(result.tokens, list)
        self.assertIsInstance(result.tokens_lower, list)
        self.assertIsInstance(result.tokens_stopped, list)
        self.assertIsInstance(result.window, str)
        self.assertIsInstance(result.record_id, str)
        self.assertIsInstance(result.token_count, int)
        self.assertIsInstance(result.stopped_count, int)


class TestWindowStopwordLoader(unittest.TestCase):
    """Tests for the WindowStopwordLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = WindowStopwordLoader()
    
    def test_valid_windows(self):
        """Test that all valid windows are recognized."""
        expected_windows = {
            "2000-2004", "2005-2009", "2010-2014", 
            "2015-2019", "2020-2024"
        }
        self.assertEqual(set(self.loader.WINDOWS), expected_windows)
    
    def test_get_stopwords_valid_window(self):
        """Test getting stopwords for a valid window."""
        stopwords = self.loader.get_stopwords("2000-2004")
        self.assertIsInstance(stopwords, set)
        self.assertGreater(len(stopwords), 0)  # Should have base stopwords
    
    def test_get_stopwords_invalid_window(self):
        """Test that invalid window raises ValueError."""
        with self.assertRaises(ValueError):
            self.loader.get_stopwords("invalid-window")
    
    def test_window_specific_stopwords(self):
        """Test that window-specific stopwords are included."""
        # Check 2020-2024 has transformer-related stopwords
        stopwords = self.loader.get_stopwords("2020-2024")
        self.assertIn("transformer", stopwords)
        self.assertIn("bert", stopwords)
        self.assertIn("llm", stopwords)
    
    def test_caching(self):
        """Test that stopwords are cached for performance."""
        # First call
        stopwords1 = self.loader.get_stopwords("2000-2004")
        # Second call should return the same object (cached)
        stopwords2 = self.loader.get_stopwords("2000-2004")
        self.assertIs(stopwords1, stopwords2)


class TestAbstractTokenizer(unittest.TestCase):
    """Tests for the AbstractTokenizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.stopword_loader = WindowStopwordLoader()
        self.tokenizer = AbstractTokenizer(self.stopword_loader)
    
    def test_clean_text_removes_urls(self):
        """Test that URLs are removed from text."""
        text = "Visit https://example.com for more info"
        cleaned = self.tokenizer.clean_text(text)
        self.assertNotIn("https://example.com", cleaned)
    
    def test_clean_text_removes_emails(self):
        """Test that email addresses are removed from text."""
        text = "Contact us at test@example.com for help"
        cleaned = self.tokenizer.clean_text(text)
        self.assertNotIn("test@example.com", cleaned)
    
    def test_tokenize_basic(self):
        """Test basic tokenization."""
        result = self.tokenizer.tokenize(
            text="This is a test abstract.",
            window="2000-2004",
            record_id="test-001"
        )
        
        self.assertEqual(result.record_id, "test-001")
        self.assertEqual(result.window, "2000-2004")
        self.assertIsInstance(result.tokens, list)
        self.assertIsInstance(result.tokens_lower, list)
        self.assertIsInstance(result.tokens_stopped, list)
    
    def test_tokenize_lowercase(self):
        """Test that tokens are lowercased."""
        result = self.tokenizer.tokenize(
            text="This Is A Test",
            window="2000-2004",
            record_id="test-001"
        )
        
        self.assertEqual(result.tokens_lower, ["this", "is", "a", "test"])
    
    def test_tokenize_removes_stopwords(self):
        """Test that stopwords are removed."""
        result = self.tokenizer.tokenize(
            text="This is a test with stopwords",
            window="2000-2004",
            record_id="test-001"
        )
        
        # "is", "a", "with" should be removed as stopwords
        self.assertNotIn("is", result.tokens_stopped)
        self.assertNotIn("a", result.tokens_stopped)
        self.assertNotIn("with", result.tokens_stopped)
    
    def test_tokenize_removes_non_alpha(self):
        """Test that non-alphabetic tokens are removed."""
        result = self.tokenizer.tokenize(
            text="Test 123 abc 456",
            window="2000-2004",
            record_id="test-001"
        )
        
        # Numbers should be removed
        for token in result.tokens_stopped:
            self.assertTrue(token.isalpha())
    
    def test_tokenize_batch(self):
        """Test batch tokenization."""
        records = [
            {"id": "1", "text": "First abstract"},
            {"id": "2", "text": "Second abstract"},
            {"id": "3", "text": "Third abstract"}
        ]
        
        results = list(self.tokenizer.tokenize_batch(records, "2000-2004"))
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].record_id, "1")
        self.assertEqual(results[1].record_id, "2")
        self.assertEqual(results[2].record_id, "3")
    
    def test_tokenize_batch_skips_invalid(self):
        """Test that batch tokenization skips invalid records."""
        records = [
            {"id": "1", "text": "Valid abstract"},
            {"id": "2", "text": None},  # Invalid
            {"id": "3", "text": "Another valid"}
        ]
        
        results = list(self.tokenizer.tokenize_batch(records, "2000-2004"))
        
        # Should only have 2 valid results
        self.assertEqual(len(results), 2)


class TestLoadPreprocessedData(unittest.TestCase):
    """Tests for the load_preprocessed_data function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_load_valid_jsonl(self):
        """Test loading a valid JSONL file."""
        # Create test data
        test_data = [
            {"id": "1", "text": "Test abstract 1"},
            {"id": "2", "text": "Test abstract 2"}
        ]
        
        jsonl_path = self.temp_path / "test.jsonl"
        with open(jsonl_path, 'w') as f:
            for record in test_data:
                f.write(json.dumps(record) + '\n')
        
        # Load data
        records = load_preprocessed_data(jsonl_path, "2000-2004")
        
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['id'], "1")
        self.assertEqual(records[1]['id'], "2")
    
    def test_load_with_alternate_field_names(self):
        """Test loading data with alternate field names."""
        test_data = [
            {"record_id": "1", "abstract": "Test abstract"}
        ]
        
        jsonl_path = self.temp_path / "test.jsonl"
        with open(jsonl_path, 'w') as f:
            for record in test_data:
                f.write(json.dumps(record) + '\n')
        
        # Load data - should normalize field names
        records = load_preprocessed_data(jsonl_path, "2000-2004")
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], "1")
        self.assertEqual(records[0]['text'], "Test abstract")
    
    def test_load_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        non_existent_path = self.temp_path / "nonexistent.jsonl"
        
        with self.assertRaises(FileNotFoundError):
            load_preprocessed_data(non_existent_path, "2000-2004")
    
    def test_load_skips_invalid_json(self):
        """Test that invalid JSON lines are skipped."""
        test_data = [
            '{"id": "1", "text": "Valid"}',
            'invalid json line',
            '{"id": "2", "text": "Also valid"}'
        ]
        
        jsonl_path = self.temp_path / "test.jsonl"
        with open(jsonl_path, 'w') as f:
            f.write('\n'.join(test_data))
        
        # Load data - should skip invalid line
        records = load_preprocessed_data(jsonl_path, "2000-2004")
        
        # Should only have 2 valid records
        self.assertEqual(len(records), 2)


class TestSaveTokenizedResults(unittest.TestCase):
    """Tests for the save_tokenized_results function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_save_results(self):
        """Test saving tokenization results."""
        results = [
            TokenizationResult(
                original_text="Test 1",
                tokens=["test", "1"],
                tokens_lower=["test", "1"],
                tokens_stopped=["test", "1"],
                window="2000-2004",
                record_id="1",
                token_count=2,
                stopped_count=2
            ),
            TokenizationResult(
                original_text="Test 2",
                tokens=["test", "2"],
                tokens_lower=["test", "2"],
                tokens_stopped=["test", "2"],
                window="2000-2004",
                record_id="2",
                token_count=2,
                stopped_count=2
            )
        ]
        
        output_path = self.temp_path / "output.jsonl"
        save_tokenized_results(results, output_path)
        
        # Verify file was created
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Parse and verify content
        record1 = json.loads(lines[0])
        self.assertEqual(record1['id'], "1")
        self.assertEqual(record1['window'], "2000-2004")
        self.assertEqual(record1['token_count'], 2)
    
    def test_save_creates_directories(self):
        """Test that save creates parent directories if needed."""
        results = [
            TokenizationResult(
                original_text="Test",
                tokens=["test"],
                tokens_lower=["test"],
                tokens_stopped=["test"],
                window="2000-2004",
                record_id="1",
                token_count=1,
                stopped_count=1
            )
        ]
        
        # Create nested path that doesn't exist
        output_path = self.temp_path / "nested" / "dir" / "output.jsonl"
        save_tokenized_results(results, output_path)
        
        # Verify file was created
        self.assertTrue(output_path.exists())


if __name__ == '__main__':
    unittest.main()