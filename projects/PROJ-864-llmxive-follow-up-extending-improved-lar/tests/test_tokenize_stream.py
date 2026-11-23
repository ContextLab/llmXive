"""
Tests for tokenize_and_stream.py
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add code root to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from data.tokenize_and_stream import count_tokens, tokenize_and_stream


class TestTokenizeStream(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_tokenizer = MagicMock()
        # Mock encode to return a list of integers of length N
        def mock_encode(text, add_special_tokens=False):
            # Simulate 1 token per word roughly, or just length based on input
            # For deterministic testing, let's say 1 token per character for simplicity
            return [1] * len(text)
        
        self.mock_tokenizer.encode.side_effect = mock_encode

    def test_count_tokens(self):
        """Test token counting function."""
        # Mock tokenizer for count_tokens
        mock_tok = MagicMock()
        mock_tok.encode.return_value = [1, 2, 3, 4, 5]
        self.assertEqual(count_tokens("hello world", mock_tok), 5)
        self.assertEqual(count_tokens("", mock_tok), 0)

    def test_tokenize_and_stream_exact_target(self):
        """Test that streaming stops exactly at token target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            target = 10
            
            # Create a generator that yields entries with known token counts
            # Entry 1: 3 tokens
            # Entry 2: 5 tokens
            # Entry 3: 4 tokens (should be truncated to 2 to hit 10)
            def mock_stream():
                yield {"text": "aaa", "source": "test"} # 3 tokens
                yield {"text": "bbbbb", "source": "test"} # 5 tokens
                yield {"text": "cccc", "source": "test"} # 4 tokens -> truncated to 2
                yield {"text": "ddddddddd", "source": "test"} # Should not be reached

            total = tokenize_and_stream(mock_stream(), self.mock_tokenizer, target, output_path)
            
            self.assertEqual(total, target)
            self.assertTrue(output_path.exists())
            
            with open(output_path, "r") as f:
                lines = f.readlines()
            
            self.assertEqual(len(lines), 3)
            
            # Check first entry
            entry1 = json.loads(lines[0])
            self.assertEqual(entry1["token_count"], 3)
            self.assertEqual(len(entry1["tokens"]), 3)
            
            # Check second entry
            entry2 = json.loads(lines[1])
            self.assertEqual(entry2["token_count"], 5)
            self.assertEqual(len(entry2["tokens"]), 5)
            
            # Check third entry (truncated)
            entry3 = json.loads(lines[2])
            self.assertEqual(entry3["token_count"], 2) # 10 - 3 - 5 = 2
            self.assertEqual(len(entry3["tokens"]), 2)

    def test_tokenize_and_stream_undershoot(self):
        """Test behavior when stream ends before target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            target = 100
            
            # Only 5 tokens available
            def mock_stream():
                yield {"text": "abc", "source": "test"} # 3 tokens
                yield {"text": "de", "source": "test"} # 2 tokens

            total = tokenize_and_stream(mock_stream(), self.mock_tokenizer, target, output_path)
            
            self.assertEqual(total, 5)
            self.assertTrue(output_path.exists())

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTokenizeStream)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    run_tests()