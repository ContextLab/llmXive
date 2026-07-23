"""
Unit tests for code/validate_citations.py
"""
import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate_citations import CitationValidator, validate_citations

class TestCitationValidator(unittest.TestCase):

    def setUp(self):
        self.valid_citations = [
            {
                "title": "Test Paper",
                "url": "https://arxiv.org/abs/2107.03374",
                "source_file": "research.md"
            }
        ]
        self.invalid_format_citations = [
            {
                "title": "Bad URL",
                "url": "not-a-url",
                "source_file": "research.md"
            }
        ]
        self.missing_url_citations = [
            {
                "title": "No URL",
                "url": "",
                "source_file": "research.md"
            }
        ]

    def test_validator_initialization(self):
        validator = CitationValidator(self.valid_citations)
        self.assertEqual(len(validator.citations), 1)
        self.assertEqual(validator.valid_count, 0)
        self.assertEqual(validator.invalid_count, 0)

    def test_url_format_valid(self):
        validator = CitationValidator(self.valid_citations)
        # Mock the reachability check to avoid network calls in unit tests
        with patch.object(validator, '_check_url_reachability', return_value=True):
            result = validator.validate()
            self.assertTrue(result)
            self.assertEqual(validator.valid_count, 1)
            self.assertEqual(validator.invalid_count, 0)

    def test_url_format_invalid(self):
        validator = CitationValidator(self.invalid_format_citations)
        result = validator.validate()
        self.assertFalse(result)
        self.assertEqual(validator.valid_count, 0)
        self.assertEqual(validator.invalid_count, 1)
        self.assertEqual(validator.validation_results[0]['reason'], "Invalid URL format")

    def test_missing_url(self):
        validator = CitationValidator(self.missing_url_citations)
        result = validator.validate()
        self.assertFalse(result)
        self.assertEqual(validator.valid_count, 0)
        self.assertEqual(validator.invalid_count, 1)
        self.assertEqual(validator.validation_results[0]['reason'], "Missing URL")

    def test_empty_citations_list(self):
        validator = CitationValidator([])
        result = validator.validate()
        self.assertFalse(result)

    def test_url_unreachable(self):
        validator = CitationValidator(self.valid_citations)
        with patch.object(validator, '_check_url_reachability', return_value=False):
            result = validator.validate()
            self.assertFalse(result)
            self.assertEqual(validator.valid_count, 0)
            self.assertEqual(validator.invalid_count, 1)
            self.assertEqual(validator.validation_results[0]['reason'], "URL unreachable (404, timeout, or network error)")

class TestValidateCitationsFunction(unittest.TestCase):
    
    @patch('validate_citations.CITATIONS_FILE_PATH', 'test_state/citations.yaml')
    def test_file_not_found(self, mock_citations_path):
        # Ensure the file doesn't exist
        if os.path.exists(mock_citations_path):
            os.remove(mock_citations_path)
        
        result = validate_citations()
        self.assertFalse(result)

    @patch('validate_citations.CITATIONS_FILE_PATH')
    def test_valid_yaml_file(self, mock_citations_path):
        # Create a temporary directory and file
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'citations.yaml')
            mock_citations_path.return_value = file_path
            
            data = [
                {"title": "Test", "url": "https://example.com", "source_file": "test.md"}
            ]
            with open(file_path, 'w') as f:
                yaml.dump(data, f)
            
            with patch('validate_citations.CitationValidator') as MockValidator:
                mock_instance = MockValidator.return_value
                mock_instance.validate.return_value = True
                mock_instance.valid_count = 1
                mock_instance.invalid_count = 0
                
                result = validate_citations()
                self.assertTrue(result)
                MockValidator.assert_called_once()

    @patch('validate_citations.CITATIONS_FILE_PATH')
    def test_invalid_yaml_content(self, mock_citations_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'citations.yaml')
            mock_citations_path.return_value = file_path
            
            # Write non-list content
            with open(file_path, 'w') as f:
                f.write("not a list")
                
            result = validate_citations()
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()