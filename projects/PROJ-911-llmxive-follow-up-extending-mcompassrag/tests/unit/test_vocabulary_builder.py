import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.vocabulary_builder import clean_text, build_fixed_vocabulary, save_vocabulary
from code.config import PROCESSED_DIR


class TestCleanText:
    def test_lowercases_text(self):
        assert clean_text("Hello World") == "hello world"

    def test_removes_special_chars(self):
        assert clean_text("Hello, World! 123") == "hello world 123"

    def test_collapse_whitespace(self):
        assert clean_text("Hello   World") == "hello world"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_none_handling(self):
        # The function expects a string, but let's ensure robustness if called with None
        # Based on implementation, it checks `if not text`
        assert clean_text(None) == ""


class TestBuildFixedVocabulary:
    def test_basic_vocabulary_building(self):
        corpus = [
            "The cat sat on the mat.",
            "The dog sat on the log.",
            "Cats and dogs are great pets."
        ]
        vocab = build_fixed_vocabulary(corpus, max_vocab_size=10)
        
        assert isinstance(vocab, set)
        # Check for expected terms
        assert "cat" in vocab or "cats" in vocab
        assert "dog" in vocab or "dogs" in vocab
        assert "sat" in vocab
        # "the" might be filtered out by max_df or min_df depending on implementation details,
        # but common nouns should be present.
        
    def test_empty_corpus(self):
        vocab = build_fixed_vocabulary([])
        assert vocab == set()

    def test_corpus_with_all_empty_strings(self):
        vocab = build_fixed_vocabulary(["", "   ", ""])
        assert vocab == set()

    def test_max_vocab_size_limit(self):
        # Create a corpus that would generate many terms
        corpus = [f"word{i} example text" for i in range(100)]
        vocab = build_fixed_vocabulary(corpus, max_vocab_size=5)
        assert len(vocab) <= 5

    def test_deterministic_output(self):
        corpus = [
            "consistent test data one",
            "consistent test data two",
            "consistent test data three"
        ]
        vocab1 = build_fixed_vocabulary(corpus, max_vocab_size=10)
        vocab2 = build_fixed_vocabulary(corpus, max_vocab_size=10)
        assert vocab1 == vocab2
