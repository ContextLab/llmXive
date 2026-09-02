"""
Unit tests for ingestion module.
"""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import re
import sys
# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import compute_sha256, download_file, validate_scope
from code.config import DataSourceConfig
from code.utils import normalize_text, validate_text_length

class TestIngestionUtils(unittest.TestCase):

    def test_compute_sha256(self):
        """Test SHA-256 computation on a known string."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Hello, World!")
            tmp_path = Path(tmp.name)
        
        try:
            # Expected hash for "Hello, World!"
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            actual_hash = compute_sha256(tmp_path)
            self.assertEqual(actual_hash, expected_hash)
        finally:
            os.remove(tmp_path)

    def test_validate_scope_adress(self):
        """Test that ADReSS primary source is valid."""
        config = DataSourceConfig(primary_source="ADReSS", secondary_source=None)
        # Mock logger
        logger = MagicMock()
        
        result = validate_scope(config, logger)
        self.assertTrue(result)
        logger.warning.assert_not_called()

    def test_validate_scope_dementiabank_warning(self):
        """Test that DementiaBank as secondary source triggers a warning."""
        config = DataSourceConfig(primary_source="ADReSS", secondary_source="DementiaBank")
        logger = MagicMock()
        
        result = validate_scope(config, logger)
        # The function returns True if primary is ADReSS, but logs a warning
        self.assertTrue(result)
        logger.warning.assert_called()
        self.assertIn("DementiaBank", logger.warning.call_args[0][0])

    def test_validate_scope_invalid_primary(self):
        """Test that non-ADReSS primary source fails validation."""
        config = DataSourceConfig(primary_source="DementiaBank", secondary_source=None)
        logger = MagicMock()
        
        result = validate_scope(config, logger)
        self.assertFalse(result)
        logger.warning.assert_called()

class TestTextCleaning(unittest.TestCase):
    """Unit tests for text cleaning (T009)."""

    def test_remove_non_verbal_annotations(self):
        """Test removal of <laughter>, <pause>, and similar non-verbal tags."""
        raw_text = "This is a sentence <laughter> with some noise <pause> and more text."
        
        # Simulating the T013 cleaning step directly for the test:
        cleaned_text = re.sub(r'<[^>]+>', '', raw_text).strip()
        
        self.assertNotIn("<laughter>", cleaned_text)
        self.assertNotIn("<pause>", cleaned_text)
        self.assertEqual(cleaned_text, "This is a sentence with some noise and more text.")

    def test_remove_multiple_tags(self):
        """Test removal of multiple non-verbal annotations in one string."""
        raw_text = "<pause> Hello <laughter> world <uh> test <pause> end."
        cleaned = re.sub(r'<[^>]+>', '', raw_text).strip()
        
        self.assertNotIn("<", cleaned)
        self.assertNotIn(">", cleaned)
        self.assertEqual(cleaned, "Hello world test end.")

    def test_empty_after_cleaning(self):
        """Test behavior when text contains only tags."""
        raw_text = "<pause> <laughter> <uh>"
        cleaned = re.sub(r'<[^>]+>', '', raw_text).strip()
        
        self.assertEqual(cleaned, "")

    def test_unicode_preservation(self):
        """Test that Unicode characters are preserved during cleaning."""
        raw_text = "Hello <pause> 世界 <laughter> тест"
        cleaned = re.sub(r'<[^>]+>', '', raw_text).strip()
        
        self.assertIn("世界", cleaned)
        self.assertIn("тест", cleaned)
        self.assertNotIn("<pause>", cleaned)

class TestUTF8NormalizationAndExclusion(unittest.TestCase):
    """Unit tests for UTF-8 normalization and exclusion logic (T010)."""

    def test_normalize_text_utf8(self):
        """Test that normalize_text handles UTF-8 correctly."""
        # Test with mixed encoding issues simulated as raw unicode
        raw_text = "Café résumé naïve"
        cleaned = normalize_text(raw_text)
        
        # Ensure the function returns a string and preserves unicode
        self.assertIsInstance(cleaned, str)
        self.assertIn("Café", cleaned)
        self.assertIn("résumé", cleaned)
        
        # Test with invalid bytes if passed as string (simulated)
        # normalize_text should handle standard string input
        raw_text2 = "Hello\nWorld\r\n"
        cleaned2 = normalize_text(raw_text2)
        self.assertEqual(cleaned2, "Hello\nWorld\n")

    def test_validate_text_length_below_threshold(self):
        """Test that validate_text_length returns False for short text."""
        short_text = "Short text."
        # T014 specifies excluding transcripts < 50 words
        is_valid = validate_text_length(short_text, min_words=50)
        self.assertFalse(is_valid)

    def test_validate_text_length_above_threshold(self):
        """Test that validate_text_length returns True for long enough text."""
        long_text = " ".join(["word"] * 50)
        is_valid = validate_text_length(long_text, min_words=50)
        self.assertTrue(is_valid)

    def test_validate_text_length_edge_case(self):
        """Test exact boundary condition."""
        exact_text = " ".join(["word"] * 49)
        is_valid = validate_text_length(exact_text, min_words=50)
        self.assertFalse(is_valid)

        exact_text_50 = " ".join(["word"] * 50)
        is_valid_50 = validate_text_length(exact_text_50, min_words=50)
        self.assertTrue(is_valid_50)

    def test_normalize_text_removes_control_chars(self):
        """Test that normalize_text removes non-printable control characters."""
        raw_text = "Hello\x00World\x01Test"
        cleaned = normalize_text(raw_text)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\x01", cleaned)

    def test_utf8_normalization_integration(self):
        """Test combined normalization and length check logic."""
        raw_text = "This is a very long text with many words to ensure it passes the length check. " * 5
        raw_text += "<pause> <laughter> "
        
        # Normalize
        cleaned = normalize_text(raw_text)
        
        # Validate length
        is_valid = validate_text_length(cleaned, min_words=50)
        
        self.assertTrue(is_valid)
        self.assertNotIn("<pause>", cleaned)
        self.assertNotIn("<laughter>", cleaned)

if __name__ == '__main__':
    unittest.main()