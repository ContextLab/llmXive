"""
Unit tests for src/lib/utils.py
"""
import logging
import random
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.lib.utils import (
    set_random_seed,
    strip_non_ascii,
    tokenize_and_truncate,
    setup_logging,
    DEFAULT_SEED,
    DEFAULT_MAX_TOKENS
)


class TestSetRandomSeed:
    def test_seed_affects_random(self):
        set_random_seed(42)
        val1 = random.random()
        
        set_random_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_seed_affects_numpy(self):
        set_random_seed(42)
        arr1 = np.random.rand(5)
        
        set_random_seed(42)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_default_seed(self):
        # Just ensure it runs without error
        set_random_seed()
        assert random.random() is not None


class TestStripNonAscii:
    def test_ascii_only(self):
        text = "Hello, World!"
        assert strip_non_ascii(text) == text

    def test_with_non_ascii(self):
        text = "Hello, Wörld! 你好"
        result = strip_non_ascii(text)
        assert "Wörld" not in result
        assert "你好" not in result
        assert "Hello, W" in result

    def test_empty_string(self):
        assert strip_non_ascii("") == ""

    def test_non_string_input(self):
        result = strip_non_ascii(123)
        assert result == "123"


class TestTokenizeAndTruncate:
    def test_no_truncation_needed(self):
        text = "hello world"
        tokens = tokenize_and_truncate(text, max_tokens=10)
        assert len(tokens) == 2
        assert tokens == ["hello", "world"]

    def test_truncation_applied(self):
        text = "a b c d e f g"
        tokens = tokenize_and_truncate(text, max_tokens=3)
        assert len(tokens) == 3
        assert tokens == ["a", "b", "c"]

    def test_empty_text(self):
        tokens = tokenize_and_truncate("")
        assert tokens == []

    def test_custom_tokenizer(self):
        def custom_tokenizer(text):
            return text.split("-")
        
        text = "hello-world-test"
        tokens = tokenize_and_truncate(text, tokenizer=custom_tokenizer)
        assert tokens == ["hello", "world", "test"]

    def test_default_max_tokens(self):
        # Create a string longer than default max tokens
        long_text = "word " * (DEFAULT_MAX_TOKENS + 10)
        tokens = tokenize_and_truncate(long_text)
        assert len(tokens) == DEFAULT_MAX_TOKENS


class TestSetupLogging:
    def test_console_handler_added(self):
        logger = setup_logging()
        assert len(logger.handlers) >= 1
        
        # Check that one handler is a StreamHandler (console)
        has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_stream

    def test_file_handler_added(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = str(Path(tmpdir) / "test.log")
            logger = setup_logging(log_file=log_path)
            
            # Check that a FileHandler was added
            has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
            assert has_file
            
            # Write a log message
            logger.info("Test message")
            
            # Verify file exists and has content
            assert os.path.exists(log_path)
            with open(log_path, "r") as f:
                content = f.read()
            assert "Test message" in content

    def test_default_level(self):
        logger = setup_logging()
        assert logger.level == logging.INFO

    def test_custom_level(self):
        logger = setup_logging(level=logging.DEBUG)
        assert logger.level == logging.DEBUG