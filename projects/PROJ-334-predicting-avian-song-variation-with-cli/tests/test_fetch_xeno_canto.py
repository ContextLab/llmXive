"""
Tests for fetch_xeno_canto.py module.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.fetch_xeno_canto import (
    extract_metadata,
    calculate_sha256,
    SAMPLE_SIZE
)

class TestExtractMetadata(unittest.TestCase):
    """Tests for the extract_metadata function."""

    def test_extract_valid_record(self):
        """Test extraction of a valid recording."""
        recordings = [
            {
                'sp': 'Turdus_migratorius',
                'lat': '40.7128',
                'lon': '-74.0060',
                'id': '12345',
                'file-type': 'mp3',
                'q': 'A'
            }
        ]
        result = extract_metadata(recordings)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['species_id'], 'Turdus_migratorius')
        self.assertEqual(result[0]['lat'], 40.7128)
        self.assertEqual(result[0]['lon'], -74.0060)
        self.assertEqual(result[0]['recording_id'], '12345')

    def test_skip_invalid_lat(self):
        """Test that records with invalid lat are skipped."""
        recordings = [
            {
                'sp': 'Turdus_migratorius',
                'lat': 'invalid',
                'lon': '-74.0060',
                'id': '12345',
                'file-type': 'mp3',
                'q': 'A'
            }
        ]
        result = extract_metadata(recordings)
        self.assertEqual(len(result), 0)

    def test_skip_missing_species(self):
        """Test that records with missing species are skipped."""
        recordings = [
            {
                'sp': None,
                'lat': '40.7128',
                'lon': '-74.0060',
                'id': '12345',
                'file-type': 'mp3',
                'q': 'A'
            }
        ]
        result = extract_metadata(recordings)
        self.assertEqual(len(result), 0)

    def test_skip_missing_coordinates(self):
        """Test that records with missing coordinates are skipped."""
        recordings = [
            {
                'sp': 'Turdus_migratorius',
                'lat': None,
                'lon': None,
                'id': '12345',
                'file-type': 'mp3',
                'q': 'A'
            }
        ]
        result = extract_metadata(recordings)
        self.assertEqual(len(result), 0)

class TestCalculateSha256(unittest.TestCase):
    """Tests for the calculate_sha256 function."""

    def test_calculate_checksum(self):
        """Test checksum calculation for a known string."""
        # Create a temporary file with known content
        test_file = Path("test_checksum.txt")
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        try:
            checksum = calculate_sha256(test_file)
            # Expected SHA256 for "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            self.assertEqual(checksum, expected)
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_nonexistent_file(self):
        """Test that calculating checksum for non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            calculate_sha256(Path("nonexistent_file.txt"))

if __name__ == '__main__':
    unittest.main()