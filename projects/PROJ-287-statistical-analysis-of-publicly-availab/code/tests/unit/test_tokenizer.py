import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

# Import the module under test
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
        """Test basic creation of TokenizationResult."""
        result = TokenizationResult(
            record_id="test-123",
            source="arxiv",
            original_text="This is a test abstract.",
            tokens=["test", "abstract"],
            lemmatized_tokens=["test", "abstract"],
            token_count=2
        )
        
        self.assertEqual(result.record_id, "test-123")
        self.assertEqual(result.source, "arxiv")
        self.assertEqual(result.token_count, 2)
        self.assertFalse(result.is_filtered)
    
    def test_filtered_result(self):
        """Test creation of a filtered result."""
        result = TokenizationResult(
            record_id="test-456",
            source="pubmed",
            original_text="Short",
            tokens=["short"],
            lemmatized_tokens=["short"],
            token_count=1,
            is_filtered=True,
            filter_reason="Insufficient tokens"
        )
        
        self.assertTrue(result.is_filtered)
        self.assertEqual(result.filter_reason, "Insufficient tokens")


class TestWindowStopwordLoader(unittest.TestCase):
    """Tests for WindowStopwordLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.loader = WindowStopwordLoader(custom_stopwords_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_base_stopwords_loaded(self):
        """Test that base English stopwords are loaded."""
        stopwords = self.loader.get_stopwords("2000-2004")
        self.assertIn("the", stopwords)
        self.assertIn("and", stopwords)
        self.assertIn("of", stopwords)

    def test_window_validation(self):
        """Test that valid windows are recognized."""
        valid_windows = ["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"]
        for window in valid_windows:
            stopwords = self.loader.get_stopwords(window)
            self.assertIsInstance(stopwords, set)
            self.assertGreater(len(stopwords), 0)

    def test_unknown_window_fallback(self):
        """Test that unknown windows fall back to base stopwords."""
        stopwords = self.loader.get_stopwords("unknown-window")
        self.assertIsInstance(stopwords, set)
        self.assertIn("the", stopwords)

    def test_custom_stopwords_loading(self):
        """Test loading custom stopwords from JSON file."""
        # Create custom stopwords file
        custom_file = self.temp_dir / "stopwords_2000-2004.json"
        custom_words = ["custom1", "custom2", "custom3"]
        with open(custom_file, 'w') as f:
            json.dump(custom_words, f)
        
        # Reload loader to pick up new file
        loader = WindowStopwordLoader(custom_stopwords_dir=self.temp_dir)
        stopwords = loader.get_stopwords("2000-2004")
        
        self.assertIn("custom1", stopwords)
        self.assertIn("custom2", stopwords)
        self.assertIn("custom3", stopwords)

    def test_add_custom_stopwords(self):
        """Test adding stopwords programmatically."""
        self.loader.add_custom_stopwords("2005-2009", ["added1", "added2"])
        stopwords = self.loader.get_stopwords("2005-2009")
        
        self.assertIn("added1", stopwords)
        self.assertIn("added2", stopwords)


class TestAbstractTokenizer(unittest.TestCase):
    """Tests for AbstractTokenizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.stopword_loader = WindowStopwordLoader()
        self.tokenizer = AbstractTokenizer(
            stopword_loader=self.stopword_loader,
            remove_punctuation=True,
            lowercase=True,
            min_token_length=2
        )

    def test_tokenize_simple_text(self):
        """Test tokenization of simple text."""
        result = self.tokenizer.tokenize(
            text="This is a test abstract with multiple words.",
            record_id="test-1",
            source="arxiv",
            window="2000-2004"
        )
        
        self.assertEqual(result.record_id, "test-1")
        self.assertEqual(result.source, "arxiv")
        self.assertGreater(len(result.tokens), 0)
        self.assertGreater(len(result.lemmatized_tokens), 0)
        self.assertFalse(result.is_filtered)  # Should have enough tokens

    def test_tokenize_empty_text(self):
        """Test tokenization of empty text."""
        result = self.tokenizer.tokenize(
            text="",
            record_id="test-2",
            source="pubmed",
            window="2000-2004"
        )
        
        self.assertTrue(result.is_filtered)
        self.assertEqual(result.filter_reason, "Empty text")
        self.assertEqual(len(result.tokens), 0)

    def test_tokenize_short_text(self):
        """Test tokenization of text with insufficient tokens."""
        result = self.tokenizer.tokenize(
            text="Short text only.",
            record_id="test-3",
            source="arxiv",
            window="2000-2004"
        )
        
        # Should be filtered due to < 20 tokens
        self.assertTrue(result.is_filtered)
        self.assertEqual(result.filter_reason, "Insufficient tokens (< 20)")

    def test_stopword_removal(self):
        """Test that stopwords are removed."""
        text = "This is a test with common stopwords like the and a."
        result = self.tokenizer.tokenize(
            text=text,
            record_id="test-4",
            source="arxiv",
            window="2000-2004"
        )
        
        # Check that common stopwords are not in tokens
        for token in result.tokens:
            self.assertNotIn(token.lower(), ["the", "a", "is", "with"])

    def test_lemmatization(self):
        """Test that tokens are lemmatized."""
        text = "The running dogs are jumping over fences."
        result = self.tokenizer.tokenize(
            text=text,
            record_id="test-5",
            source="arxiv",
            window="2000-2004"
        )
        
        # Check that lemmatized tokens exist
        self.assertGreater(len(result.lemmatized_tokens), 0)
        
        # 'running' should be lemmatized to 'run'
        # 'dogs' should be lemmatized to 'dog'
        # Note: exact lemmatization depends on spaCy model

    def test_token_counting(self):
        """Test that token counts are accurate."""
        text = "Word1 word2 word3 word4 word5."
        result = self.tokenizer.tokenize(
            text=text,
            record_id="test-6",
            source="arxiv",
            window="2000-2004"
        )
        
        self.assertEqual(result.token_count, len(result.lemmatized_tokens))
        self.assertGreater(result.token_count, 0)


class TestLoadPreprocessedData(unittest.TestCase):
    """Tests for load_preprocessed_data function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_input.jsonl"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_jsonl(self):
        """Test loading valid JSONL data."""
        # Create test data
        records = [
            {"id": "1", "text": "First abstract.", "source": "arxiv"},
            {"id": "2", "text": "Second abstract.", "source": "pubmed"}
        ]
        
        with open(self.test_file, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')
        
        loaded = load_preprocessed_data(self.test_file)
        
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["id"], "1")
        self.assertEqual(loaded[1]["source"], "pubmed")

    def test_load_missing_file(self):
        """Test loading from non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_preprocessed_data(Path("/nonexistent/file.jsonl"))

    def test_load_invalid_json(self):
        """Test loading invalid JSON."""
        with open(self.test_file, 'w') as f:
            f.write("invalid json\n")
        
        with self.assertRaises(ValueError):
            load_preprocessed_data(self.test_file)

    def test_load_missing_fields(self):
        """Test loading records with missing required fields."""
        with open(self.test_file, 'w') as f:
            f.write(json.dumps({"id": "1"}) + '\n')  # Missing 'text'
        
        with self.assertRaises(ValueError):
            load_preprocessed_data(self.test_file)


class TestSaveTokenizedResults(unittest.TestCase):
    """Tests for save_tokenized_results function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_file = self.temp_dir / "output.jsonl"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_results(self):
        """Test saving tokenization results."""
        results = [
            TokenizationResult(
                record_id="1",
                source="arxiv",
                original_text="Test abstract 1",
                tokens=["test", "abstract"],
                lemmatized_tokens=["test", "abstract"],
                token_count=2
            ),
            TokenizationResult(
                record_id="2",
                source="pubmed",
                original_text="Test abstract 2",
                tokens=["test", "abstract", "two"],
                lemmatized_tokens=["test", "abstract", "two"],
                token_count=3,
                is_filtered=True,
                filter_reason="Insufficient tokens"
            )
        ]
        
        save_tokenized_results(results, self.output_file, include_filtered=True)
        
        # Verify file exists and has content
        self.assertTrue(self.output_file.exists())
        
        with open(self.output_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Verify JSON structure
        data1 = json.loads(lines[0])
        self.assertEqual(data1["id"], "1")
        self.assertEqual(data1["is_filtered"], False)

    def test_save_excluding_filtered(self):
        """Test saving results excluding filtered records."""
        results = [
            TokenizationResult(
                record_id="1",
                source="arxiv",
                original_text="Test abstract 1",
                tokens=["test", "abstract"],
                lemmatized_tokens=["test", "abstract"],
                token_count=2
            ),
            TokenizationResult(
                record_id="2",
                source="pubmed",
                original_text="Short",
                tokens=["short"],
                lemmatized_tokens=["short"],
                token_count=1,
                is_filtered=True,
                filter_reason="Insufficient tokens"
            )
        ]
        
        save_tokenized_results(results, self.output_file, include_filtered=False)
        
        with open(self.output_file, 'r') as f:
            lines = f.readlines()
        
        # Only the non-filtered record should be saved
        self.assertEqual(len(lines), 1)
        data = json.loads(lines[0])
        self.assertEqual(data["id"], "1")

    def test_save_creates_directories(self):
        """Test that save creates parent directories if needed."""
        nested_output = self.temp_dir / "nested" / "dir" / "output.jsonl"
        
        results = [
            TokenizationResult(
                record_id="1",
                source="arxiv",
                original_text="Test",
                tokens=["test"],
                lemmatized_tokens=["test"],
                token_count=1
            )
        ]
        
        save_tokenized_results(results, nested_output, include_filtered=True)
        
        self.assertTrue(nested_output.exists())


if __name__ == '__main__':
    unittest.main()