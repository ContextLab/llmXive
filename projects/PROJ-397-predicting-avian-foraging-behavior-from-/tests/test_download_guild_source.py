"""
Unit tests for download_guild_source module.
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import csv
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download_guild_source import (
    validate_guild_source,
    REQUIRED_COLUMNS,
    load_metadata_config
)
from utils.config import get_raw_data_dir, get_metadata_file


class TestDownloadGuildSource(unittest.TestCase):
    """Test cases for download_guild_source module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "test_guilds.csv"
        
        # Create a valid test CSV
        with open(self.test_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["species_id", "foraging_guild"])
            writer.writeheader()
            writer.writerow({"species_id": "sp001", "foraging_guild": "granivore"})
            writer.writerow({"species_id": "sp002", "foraging_guild": "insectivore"})
            writer.writerow({"species_id": "sp003", "foraging_guild": "frugivore"})

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_guild_source_valid_file(self):
        """Test validation passes for a valid CSV file."""
        # Should not raise any exception
        try:
            validate_guild_source(self.test_csv_path)
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success, "Validation should pass for valid CSV")

    def test_validate_guild_source_missing_columns(self):
        """Test validation fails when required columns are missing."""
        # Create CSV with missing columns
        invalid_csv_path = Path(self.temp_dir) / "invalid_guilds.csv"
        with open(invalid_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["species_id"])
            writer.writeheader()
            writer.writerow({"species_id": "sp001"})
        
        with self.assertRaises(ValueError) as context:
            validate_guild_source(invalid_csv_path)
        
        self.assertIn("Missing required columns", str(context.exception))

    def test_validate_guild_source_empty_file(self):
        """Test validation fails for an empty CSV file."""
        empty_csv_path = Path(self.temp_dir) / "empty_guilds.csv"
        with open(empty_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["species_id", "foraging_guild"])
            writer.writeheader()
            # No data rows
        
        with self.assertRaises(ValueError) as context:
            validate_guild_source(empty_csv_path)
        
        self.assertIn("CSV file is empty", str(context.exception))

    def test_validate_guild_source_file_not_found(self):
        """Test validation fails when file does not exist."""
        non_existent_path = Path(self.temp_dir) / "non_existent.csv"
        
        with self.assertRaises(FileNotFoundError):
            validate_guild_source(non_existent_path)

    def test_validate_guild_source_invalid_csv_format(self):
        """Test validation fails for malformed CSV."""
        malformed_csv_path = Path(self.temp_dir) / "malformed_guilds.csv"
        with open(malformed_csv_path, 'w', encoding='utf-8') as f:
            f.write("species_id,foraging_guild\nsp001,granivore\nsp002,insectivore,extra_column")
        
        # This should raise a CSV error
        with self.assertRaises(ValueError):
            validate_guild_source(malformed_csv_path)

    def test_required_columns_constant(self):
        """Test that REQUIRED_COLUMNS contains expected values."""
        self.assertIn("species_id", REQUIRED_COLUMNS)
        self.assertIn("foraging_guild", REQUIRED_COLUMNS)
        self.assertEqual(len(REQUIRED_COLUMNS), 2)


if __name__ == '__main__':
    unittest.main()