"""
Unit tests for the tokenizer module.

Tests cover:
- TokenizationResult dataclass
- WindowStopwordLoader functionality
- AbstractTokenizer tokenization logic
- File I/O operations
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.preprocess.tokenizer import (
    TokenizationResult,
    WindowStopwordLoader,
    AbstractTokenizer,
    load_preprocessed_data,
    save_tokenized_results
)


class TestTokenizationResult(unittest.TestCase):
    """Tests for the TokenizationResult dataclass."""
    
    def test_successful_tokenization(self):
        """Test creating a successful tokenization result."""
        result = TokenizationResult(
            original_id="test-123",
            window="2000-2004",
            tokens=["test", "tokens"],
            token_count=2,
            filtered_tokens=["test"],
            filtered_count=1,
            success=True
        )
        
        self.assertEqual(result.original_id, "test-123")
        self.assertEqual(result.window, "2000-2004")
        self.assertEqual(result.tokens, ["test", "tokens"])
        self.assertEqual(result.token_count, 2)
        self.assertEqual(result.filtered_tokens, ["test"])
        self.assertEqual(result.filtered_count, 1)
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
    
    def test_failed_tokenization(self):
        """Test creating a failed tokenization result."""
        result = TokenizationResult(
            original_id="test-456",
            window="2005-2009",
            tokens=[],
            token_count=0,
            filtered_tokens=[],
            filtered_count=0,
            success=False,
            error_message="Test error"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Test error")
        self.assertEqual(result.token_count, 0)
        self.assertEqual(result.filtered_count, 0)


class TestWindowStopwordLoader(unittest.TestCase):
    """Tests for the WindowStopwordLoader class."""
    
    def setUp(self):
        """Set up temporary directory and manifest."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stopwords_dir = Path(self.temp_dir.name)
        
        # Create manifest
        self.manifest_path = self.stopwords_dir / "manifest.json"
        manifest_data = {
            "windows": [
                {
                    "window_id": "2000-2004",
                    "checksum": "abc123"
                },
                {
                    "window_id": "2005-2009",
                    "checksum": "def456"
                }
            ]
        }
        
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create stopword files
        for window_id in ["2000-2004", "2005-2009"]:
            stopwords_file = self.stopwords_dir / f"{window_id}_stopwords.json"
            stopwords_data = {
                "window_id": window_id,
                "stopwords": ["the", "and", "of"]
            }
            with open(stopwords_file, 'w') as f:
                json.dump(stopwords_data, f)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_load_manifest(self):
        """Test loading the stopword manifest."""
        loader = WindowStopwordLoader(self.manifest_path)
        
        self.assertEqual(len(loader.manifest['windows']), 2)
        self.assertIn('windows', loader.manifest)
    
    def test_get_stopwords_valid_window(self):
        """Test getting stopwords for a valid window."""
        loader = WindowStopwordLoader(self.manifest_path)
        
        stopwords = loader.get_stopwords("2000-2004")
        
        self.assertIsInstance(stopwords, set)
        self.assertIn("the", stopwords)
        self.assertIn("and", stopwords)
        self.assertIn("of", stopwords)
        self.assertEqual(len(stopwords), 3)
    
    def test_get_stopwords_cached(self):
        """Test that stopwords are cached after first load."""
        loader = WindowStopwordLoader(self.manifest_path)
        
        # First load
        stopwords1 = loader.get_stopwords("2000-2004")
        # Second load (should be cached)
        stopwords2 = loader.get_stopwords("2000-2004")
        
        self.assertIs(stopwords1, stopwords2)
    
    def test_get_stopwords_invalid_window(self):
        """Test that invalid window raises KeyError."""
        loader = WindowStopwordLoader(self.manifest_path)
        
        with self.assertRaises(KeyError):
            loader.get_stopwords("invalid-window")
    
    def test_missing_manifest(self):
        """Test that missing manifest raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            WindowStopwordLoader(Path("/nonexistent/manifest.json"))
    
    def test_missing_stopword_file(self):
        """Test that missing stopword file raises FileNotFoundError."""
        # Create manifest without corresponding stopword file
        manifest_data = {
            "windows": [
                {"window_id": "2010-2014", "checksum": "xyz789"}
            ]
        }
        manifest_path = self.stopwords_dir / "manifest_missing.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        loader = WindowStopwordLoader(manifest_path)
        
        with self.assertRaises(FileNotFoundError):
            loader.get_stopwords("2010-2014")

class TestAbstractTokenizer(unittest.TestCase):
    """Tests for the AbstractTokenizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stopwords_dir = Path(self.temp_dir.name)
        
        # Create manifest and stopword files
        self.manifest_path = self.stopwords_dir / "manifest.json"
        manifest_data = {
            "windows": [
                {"window_id": "2000-2004", "checksum": "abc123"}
            ]
        }
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        stopwords_file = self.stopwords_dir / "2000-2004_stopwords.json"
        stopwords_data = {
            "window_id": "2000-2004",
            "stopwords": ["the", "and", "of", "a"]
        }
        with open(stopwords_file, 'w') as f:
            json.dump(stopwords_data, f)
        
        # Mock the WindowStopwordLoader to avoid loading actual stopwords
        self.patch_loader = patch(
            'src.data.preprocess.tokenizer.WindowStopwordLoader'
        )
        self.mock_loader_class = self.patch_loader.start()
        self.mock_loader_instance = MagicMock()
        self.mock_loader_instance.get_stopwords.return_value = {"the", "and", "of", "a"}
        self.mock_loader_class.return_value = self.mock_loader_instance
    
    def tearDown(self):
        """Clean up."""
        self.patch_loader.stop()
        self.temp_dir.cleanup()
    
    @patch('src.data.preprocess.tokenizer.spacy.load')
    def test_tokenize_basic(self, mock_spacy_load):
        """Test basic tokenization."""
        # Mock spaCy
        mock_doc = MagicMock()
        mock_token1 = MagicMock()
        mock_token1.is_space = False
        mock_token1.is_punct = False
        mock_token1.text = "Hello"
        mock_token1.lemma_ = "hello"
        
        mock_token2 = MagicMock()
        mock_token2.is_space = False
        mock_token2.is_punct = False
        mock_token2.text = "world"
        mock_token2.lemma_ = "world"
        
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_token1, mock_token2]))
        mock_spacy_load.return_value = mock_doc
        
        tokenizer = AbstractTokenizer()
        abstract = {"id": "test-1", "text": "Hello world"}
        
        result = tokenizer.tokenize(abstract, "2000-2004")
        
        self.assertTrue(result.success)
        self.assertEqual(result.original_id, "test-1")
        self.assertEqual(result.window, "2000-2004")
        self.assertEqual(result.token_count, 2)
        self.assertEqual(result.filtered_count, 2)
    
    @patch('src.data.preprocess.tokenizer.spacy.load')
    def test_tokenize_with_stopwords(self, mock_spacy_load):
        """Test that stopwords are filtered out."""
        # Mock spaCy with stopwords
        mock_doc = MagicMock()
        mock_token1 = MagicMock()
        mock_token1.is_space = False
        mock_token1.is_punct = False
        mock_token1.text = "The"
        mock_token1.lemma_ = "the"
        
        mock_token2 = MagicMock()
        mock_token2.is_space = False
        mock_token2.is_punct = False
        mock_token2.text = "test"
        mock_token2.lemma_ = "test"
        
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_token1, mock_token2]))
        mock_spacy_load.return_value = mock_doc
        
        tokenizer = AbstractTokenizer()
        abstract = {"id": "test-2", "text": "The test"}
        
        result = tokenizer.tokenize(abstract, "2000-2004")
        
        self.assertTrue(result.success)
        self.assertEqual(result.token_count, 2)
        self.assertEqual(result.filtered_count, 1)
        self.assertIn("test", result.filtered_tokens)
        self.assertNotIn("the", result.filtered_tokens)
    
    @patch('src.data.preprocess.tokenizer.spacy.load')
    def test_tokenize_empty_text(self, mock_spacy_load):
        """Test tokenization with empty text."""
        tokenizer = AbstractTokenizer()
        abstract = {"id": "test-3", "text": ""}
        
        result = tokenizer.tokenize(abstract, "2000-2004")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Empty text")
        self.assertEqual(result.token_count, 0)
        self.assertEqual(result.filtered_count, 0)
    
    @patch('src.data.preprocess.tokenizer.spacy.load')
    def test_tokenize_clean_text(self, mock_spacy_load):
        """Test that text cleaning works correctly."""
        # Mock spaCy
        mock_doc = MagicMock()
        mock_token = MagicMock()
        mock_token.is_space = False
        mock_token.is_punct = False
        mock_token.text = "test"
        mock_token.lemma_ = "test"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_token]))
        mock_spacy_load.return_value = mock_doc
        
        tokenizer = AbstractTokenizer()
        abstract = {"id": "test-4", "text": "Test with URL http://example.com and email test@test.com"}
        
        result = tokenizer.tokenize(abstract, "2000-2004")
        
        self.assertTrue(result.success)
        self.assertNotIn("http", result.filtered_tokens)
        self.assertNotIn("example", result.filtered_tokens)
        self.assertNotIn("test@test.com", result.filtered_tokens)
    
    @patch('src.data.preprocess.tokenizer.spacy.load')
    def test_tokenize_lemmatization(self, mock_spacy_load):
        """Test that lemmatization is applied."""
        mock_doc = MagicMock()
        mock_token = MagicMock()
        mock_token.is_space = False
        mock_token.is_punct = False
        mock_token.text = "running"
        mock_token.lemma_ = "run"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_token]))
        mock_spacy_load.return_value = mock_doc
        
        tokenizer = AbstractTokenizer()
        abstract = {"id": "test-5", "text": "running"}
        
        result = tokenizer.tokenize(abstract, "2000-2004")
        
        self.assertTrue(result.success)
        self.assertIn("run", result.filtered_tokens)
        self.assertNotIn("running", result.filtered_tokens)

class TestLoadPreprocessedData(unittest.TestCase):
    """Tests for load_preprocessed_data function."""
    
    def setUp(self):
        """Set up temporary file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test.jsonl"
        
        test_data = [
            {"id": "1", "text": "Test abstract one"},
            {"id": "2", "text": "Test abstract two"},
            {"id": "3", "text": "Test abstract three"}
        ]
        
        with open(self.test_file, 'w') as f:
            for record in test_data:
                f.write(json.dumps(record) + '\n')
    
    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()
    
    def test_load_valid_file(self):
        """Test loading a valid JSONL file."""
        abstracts = load_preprocessed_data(self.test_file)
        
        self.assertEqual(len(abstracts), 3)
        self.assertEqual(abstracts[0]['id'], "1")
        self.assertEqual(abstracts[1]['id'], "2")
        self.assertEqual(abstracts[2]['id'], "3")
    
    def test_load_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_preprocessed_data(Path("/nonexistent/file.jsonl"))
    
    def test_load_with_empty_lines(self):
        """Test loading file with empty lines."""
        # Add empty lines to file
        with open(self.test_file, 'a') as f:
            f.write('\n')
            f.write('\n')
        
        abstracts = load_preprocessed_data(self.test_file)
        
        self.assertEqual(len(abstracts), 3)  # Should ignore empty lines

class TestSaveTokenizedResults(unittest.TestCase):
    """Tests for save_tokenized_results function."""
    
    def setUp(self):
        """Set up temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_file = Path(self.temp_dir.name) / "output.jsonl"
    
    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()
    
    def test_save_results(self):
        """Test saving tokenization results."""
        results = [
            TokenizationResult(
                original_id="test-1",
                window="2000-2004",
                tokens=["test", "tokens"],
                token_count=2,
                filtered_tokens=["test"],
                filtered_count=1,
                success=True
            ),
            TokenizationResult(
                original_id="test-2",
                window="2000-2004",
                tokens=[],
                token_count=0,
                filtered_tokens=[],
                filtered_count=0,
                success=False,
                error_message="Test error"
            )
        ]
        
        save_tokenized_results(results, self.output_file)
        
        self.assertTrue(self.output_file.exists())
        
        # Verify saved content
        with open(self.output_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        record1 = json.loads(lines[0])
        self.assertEqual(record1['id'], "test-1")
        self.assertEqual(record1['success'], True)
        self.assertEqual(record1['filtered_count'], 1)
        
        record2 = json.loads(lines[1])
        self.assertEqual(record2['id'], "test-2")
        self.assertEqual(record2['success'], False)
        self.assertEqual(record2['error'], "Test error")
    
    def test_save_creates_directories(self):
        """Test that save creates parent directories if needed."""
        nested_path = Path(self.temp_dir.name) / "nested" / "path" / "output.jsonl"
        
        results = [
            TokenizationResult(
                original_id="test-1",
                window="2000-2004",
                tokens=[],
                token_count=0,
                filtered_tokens=[],
                filtered_count=0,
                success=True
            )
        ]
        
        save_tokenized_results(results, nested_path)
        
        self.assertTrue(nested_path.exists())

if __name__ == '__main__':
    unittest.main()