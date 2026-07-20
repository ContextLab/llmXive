import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.preprocess.tokenizer import (
    TokenizationResult,
    WindowStopwordLoader,
    AbstractTokenizer,
    load_preprocessed_data,
    save_tokenized_results
)

class TestTokenizationResult(unittest.TestCase):
    def test_tokenization_result_creation(self):
        result = TokenizationResult(
            original_text="test",
            tokens=["test"],
            lemmas=["test"],
            window="2000-2004",
            source="arxiv",
            record_id="123",
            token_count=1
        )
        self.assertEqual(result.token_count, 1)
        self.assertEqual(result.window, "2000-2004")

class TestWindowStopwordLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.stopword_file = self.temp_dir / "2000-2004_stopwords.txt"
        self.stopword_file.write_text("test_word\nanother_word\n")

    def test_load_stopwords(self):
        loader = WindowStopwordLoader(self.temp_dir)
        stopwords = loader.get_stopwords("2000-2004")
        self.assertIn("test_word", stopwords)
        self.assertIn("another_word", stopwords)
        # Should include NLTK stopwords too
        self.assertIn("the", stopwords)

    def test_cache(self):
        loader = WindowStopwordLoader(self.temp_dir)
        # Call twice
        s1 = loader.get_stopwords("2000-2004")
        s2 = loader.get_stopwords("2000-2004")
        self.assertIs(s1, s2)

    def test_missing_file(self):
        # Create a loader for a window with no file
        loader = WindowStopwordLoader(self.temp_dir)
        # Should not raise, just use base stopwords
        stopwords = loader.get_stopwords("nonexistent-window")
        self.assertIn("the", stopwords)

class TestAbstractTokenizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.stopword_file = self.temp_dir / "2000-2004_stopwords.txt"
        self.stopword_file.write_text("test_stop\n")
        self.loader = WindowStopwordLoader(self.temp_dir)
        self.tokenizer = AbstractTokenizer(self.loader)

    def test_clean_text(self):
        text = "Hello World! Visit http://example.com"
        cleaned = self.tokenizer._clean_text(text)
        self.assertEqual(cleaned, "hello world  visit ")
        self.assertNotIn("http", cleaned)

    def test_tokenize_and_lemmatize(self):
        text = "The cats are running quickly."
        tokens = self.tokenizer._tokenize_with_nltk(text)
        self.assertIn("cats", tokens)
        self.assertIn("running", tokens)
        
        lemmas = self.tokenizer._lemmatize_tokens(tokens)
        # "cats" -> "cat", "running" -> "run"
        self.assertIn("cat", lemmas)
        self.assertIn("run", lemmas)

    def test_remove_stopwords(self):
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        stopwords = {"the", "on"}
        filtered = self.tokenizer._remove_stopwords(tokens, stopwords)
        self.assertNotIn("the", filtered)
        self.assertNotIn("on", filtered)
        self.assertIn("cat", filtered)

    def test_tokenize_record(self):
        record = {
            "text": "The cat sat on the mat.",
            "source": "arxiv",
            "id": "123"
        }
        result = self.tokenizer.tokenize_record(record, "2000-2004")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.window, "2000-2004")
        self.assertEqual(result.source, "arxiv")
        self.assertEqual(result.record_id, "123")
        self.assertIn("cat", result.lemmas)
        self.assertNotIn("the", result.lemmas)

    def test_tokenize_record_empty(self):
        record = {"text": "", "source": "arxiv", "id": "123"}
        result = self.tokenizer.tokenize_record(record, "2000-2004")
        self.assertIsNone(result)

class TestLoadPreprocessedData(unittest.TestCase):
    def test_load_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": "1", "text": "test"}\n')
            f.write('{"id": "2", "text": "test2"}\n')
            path = Path(f.name)

        records = list(load_preprocessed_data(path))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["id"], "1")
        self.unlink(path)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            list(load_preprocessed_data(Path("nonexistent.jsonl")))

    def unlink(self, path):
        path.unlink()

class TestSaveTokenizedResults(unittest.TestCase):
    def test_save_results(self):
        results = [
            TokenizationResult(
                original_text="test",
                tokens=["test"],
                lemmas=["test"],
                window="2000-2004",
                source="arxiv",
                record_id="123",
                token_count=1
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.jsonl"
            save_tokenized_results(results, output_path)
            
            self.assertTrue(output_path.exists())
            with open(output_path) as f:
                line = f.readline()
                data = json.loads(line)
                self.assertEqual(data["id"], "123")
                self.assertEqual(data["window"], "2000-2004")

if __name__ == "__main__":
    unittest.main()