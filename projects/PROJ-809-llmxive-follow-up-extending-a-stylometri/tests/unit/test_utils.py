"""
Unit tests for code/utils.py
"""
import hashlib
import json
import os
import string
import tempfile
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from utils import (
    compute_sha256,
    compute_sha256_string,
    tokenize_char_level_no_punct,
    save_json,
    load_json,
    get_logger
)


class TestSha256:
    def test_compute_sha256_string(self):
        """Test SHA-256 of a known string."""
        text = "Hello, World!"
        expected = hashlib.sha256(text.encode('utf-8')).hexdigest()
        assert compute_sha256_string(text) == expected

    def test_compute_sha256_file(self):
        """Test SHA-256 of a temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            expected = hashlib.sha256(b"Test content").hexdigest()
            assert compute_sha256(temp_path) == expected
        finally:
            os.unlink(temp_path)


class TestTokenization:
    def test_lower_case_conversion(self):
        """Test that input is converted to lowercase."""
        text = "Hello WORLD"
        tokens = tokenize_char_level_no_punct(text)
        assert all(t.islower() or t == ' ' for t in tokens)

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        text = "Hello, World! How are you?"
        tokens = tokenize_char_level_no_punct(text)
        # Check no punctuation characters are present
        for t in tokens:
            assert t not in string.punctuation

    def test_space_preservation(self):
        """Test that spaces are preserved."""
        text = "A B"
        tokens = tokenize_char_level_no_punct(text)
        assert ' ' in tokens
        assert 'a' in tokens
        assert 'b' in tokens

    def test_empty_string(self):
        """Test tokenization of empty string."""
        tokens = tokenize_char_level_no_punct("")
        assert tokens == []

    def test_pure_punctuation(self):
        """Test tokenization of pure punctuation."""
        text = "!!!???"
        tokens = tokenize_char_level_no_punct(text)
        assert tokens == []


class TestJsonUtils:
    def test_save_and_load_json(self):
        """Test saving and loading JSON."""
        data = {"key": "value", "number": 123}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)

        try:
            save_json(data, temp_path)
            loaded_data = load_json(temp_path)
            assert loaded_data == data
        finally:
            os.unlink(temp_path)


class TestLogger:
    def test_get_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"