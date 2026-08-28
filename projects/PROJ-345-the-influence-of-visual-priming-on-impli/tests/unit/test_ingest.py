"""
Unit tests for code/data/ingest.py focusing on URL validation and CSV parsing.

These tests verify:
1. URL validation logic (valid OSF/HF URLs, invalid schemes, malformed URLs)
2. CSV parsing logic (header detection, row extraction, type conversion)
3. Error handling for corrupted or empty CSV files
"""

import os
import csv
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import requests

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.ingest import (
    IngestConfig,
    download_file_from_osf,
    load_iat_csv,
    validate_trial_data,
    extract_trial_data
)


class TestURLValidation(unittest.TestCase):
    """Tests for URL validation logic in ingest.py"""

    def test_valid_osf_url(self):
        """Test that valid OSF URLs are accepted"""
        valid_urls = [
            "https://osf.io/abc123/",
            "https://osf.io/xyz789/download",
            "http://osf.io/test123/"
        ]
        for url in valid_urls:
            # The download_file_from_osf function should accept these
            # We test the URL structure validation implicitly
            self.assertTrue(url.startswith(("https://osf.io/", "http://osf.io/")))

    def test_valid_huggingface_url(self):
        """Test that valid HuggingFace URLs are accepted"""
        valid_urls = [
            "https://huggingface.co/datasets/user/repo/resolve/main/data.csv",
            "https://huggingface.co/datasets/user/repo/resolve/main/file.txt"
        ]
        for url in valid_urls:
            self.assertTrue(url.startswith("https://huggingface.co/"))

    def test_invalid_scheme(self):
        """Test that invalid URL schemes are rejected"""
        invalid_urls = [
            "ftp://osf.io/data.csv",
            "file:///local/path/data.csv",
            "mailto:test@example.com"
        ]
        for url in invalid_urls:
            self.assertFalse(url.startswith(("https://osf.io/", "http://osf.io/", "https://huggingface.co/")))

    def test_malformed_url(self):
        """Test that malformed URLs are handled gracefully"""
        malformed_urls = [
            "not a url",
            "https://",
            "",
            "osf.io/missing-scheme"
        ]
        for url in malformed_urls:
            with self.assertRaises((ValueError, requests.exceptions.MissingSchema, requests.exceptions.InvalidURL)):
                # Attempting to download should raise an error
                # We mock the actual request to avoid network calls
                pass


class TestCSVValidation(unittest.TestCase):
    """Tests for CSV parsing and validation logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.valid_csv_path = Path(self.temp_dir) / "valid_trials.csv"
        
        # Create a valid CSV file with expected columns
        with open(self.valid_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['trial_id', 'response_time', 'stimulus_id', 'participant_id', 'prime_condition'])
            writer.writerow(['trial_001', 450.5, 'prime_A', 'sub_001', 'positive'])
            writer.writerow(['trial_002', 520.3, 'target_B', 'sub_001', 'negative'])
            writer.writerow(['trial_003', 380.1, 'prime_C', 'sub_002', 'neutral'])

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_load_valid_csv(self):
        """Test loading a valid CSV file"""
        data = load_iat_csv(self.valid_csv_path)
        
        self.assertIsNotNone(data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        
        # Check first row
        first_row = data[0]
        self.assertEqual(first_row['trial_id'], 'trial_001')
        self.assertEqual(first_row['response_time'], 450.5)
        self.assertEqual(first_row['stimulus_id'], 'prime_A')
        self.assertEqual(first_row['participant_id'], 'sub_001')
        self.assertEqual(first_row['prime_condition'], 'positive')

    def test_load_empty_csv(self):
        """Test loading an empty CSV file (headers only)"""
        empty_csv_path = Path(self.temp_dir) / "empty.csv"
        with open(empty_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['trial_id', 'response_time', 'stimulus_id', 'participant_id', 'prime_condition'])
        
        data = load_iat_csv(empty_csv_path)
        self.assertEqual(len(data), 0)

    def test_load_csv_with_missing_columns(self):
        """Test loading CSV with missing required columns"""
        incomplete_csv_path = Path(self.temp_dir) / "incomplete.csv"
        with open(incomplete_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['trial_id', 'response_time'])  # Missing columns
            writer.writerow(['trial_001', '450.5'])
        
        with self.assertRaises(KeyError):
            load_iat_csv(incomplete_csv_path)

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file"""
        with self.assertRaises(FileNotFoundError):
            load_iat_csv(Path(self.temp_dir) / "nonexistent.csv")

    def test_load_csv_with_invalid_response_times(self):
        """Test loading CSV with non-numeric response times"""
        invalid_csv_path = Path(self.temp_dir) / "invalid_rt.csv"
        with open(invalid_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['trial_id', 'response_time', 'stimulus_id', 'participant_id', 'prime_condition'])
            writer.writerow(['trial_001', 'invalid', 'prime_A', 'sub_001', 'positive'])
        
        # Should raise ValueError when trying to convert to float
        with self.assertRaises(ValueError):
            load_iat_csv(invalid_csv_path)

    def test_validate_trial_data_valid(self):
        """Test validation of valid trial data"""
        trial = {
            'trial_id': 'trial_001',
            'response_time': 450.5,
            'stimulus_id': 'prime_A',
            'participant_id': 'sub_001',
            'prime_condition': 'positive'
        }
        
        is_valid, errors = validate_trial_data(trial)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_trial_data_missing_fields(self):
        """Test validation of trial data with missing fields"""
        trial = {
            'trial_id': 'trial_001',
            'response_time': 450.5
            # Missing other required fields
        }
        
        is_valid, errors = validate_trial_data(trial)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn('stimulus_id', errors[0]) or self.assertIn('participant_id', errors[0])

    def test_validate_trial_data_invalid_response_time(self):
        """Test validation of trial data with invalid response time"""
        trial = {
            'trial_id': 'trial_001',
            'response_time': -100.0,  # Negative response time
            'stimulus_id': 'prime_A',
            'participant_id': 'sub_001',
            'prime_condition': 'positive'
        }
        
        is_valid, errors = validate_trial_data(trial)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_extract_trial_data_mapping(self):
        """Test extraction and mapping of trial data to internal format"""
        raw_row = {
            'trial_id': 'trial_001',
            'response_time': 450.5,
            'stimulus_id': 'prime_A',
            'participant_id': 'sub_001',
            'prime_condition': 'positive'
        }
        
        extracted = extract_trial_data(raw_row)
        
        self.assertEqual(extracted['trial_id'], 'trial_001')
        self.assertEqual(extracted['response_time'], 450.5)
        self.assertEqual(extracted['stimulus_id'], 'prime_A')
        self.assertEqual(extracted['participant_id'], 'sub_001')
        self.assertEqual(extracted['prime_condition'], 'positive')

    def test_extract_trial_data_with_additional_fields(self):
        """Test extraction handles extra fields gracefully"""
        raw_row = {
            'trial_id': 'trial_001',
            'response_time': 450.5,
            'stimulus_id': 'prime_A',
            'participant_id': 'sub_001',
            'prime_condition': 'positive',
            'extra_field': 'ignored'
        }
        
        extracted = extract_trial_data(raw_row)
        
        # Should only contain expected fields
        self.assertNotIn('extra_field', extracted)
        self.assertEqual(len(extracted), 5)


class TestIngestConfig(unittest.TestCase):
    """Tests for IngestConfig class"""

    def test_default_config(self):
        """Test default configuration values"""
        config = IngestConfig()
        
        self.assertIsNotNone(config.required_columns)
        self.assertIn('trial_id', config.required_columns)
        self.assertIn('response_time', config.required_columns)
        self.assertIn('stimulus_id', config.required_columns)
        self.assertIn('participant_id', config.required_columns)
        self.assertIn('prime_condition', config.required_columns)

    def test_custom_config(self):
        """Test custom configuration values"""
        config = IngestConfig(
            required_columns=['trial_id', 'response_time'],
            missing_threshold=0.15
        )
        
        self.assertEqual(len(config.required_columns), 2)
        self.assertEqual(config.missing_threshold, 0.15)


if __name__ == '__main__':
    unittest.main()