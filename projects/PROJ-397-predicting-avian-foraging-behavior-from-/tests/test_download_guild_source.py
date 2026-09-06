"""
Unit tests for download_guild_source.py
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import csv
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.download_guild_source import (
    validate_guild_source,
    load_metadata_config,
    compute_sha256
)
from utils.config import get_raw_data_dir, get_metadata_file

class TestDownloadGuildSource(unittest.TestCase):
    """Test suite for guild source download functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_data_dir = Path(self.test_dir) / "raw"
        self.raw_data_dir.mkdir()
        
        # Create a mock metadata file
        self.metadata_file = Path(self.test_dir) / "metadata.yaml"
        self.metadata_file.write_text("sources: {}\nartifacts: {}\n")

        # Mock the config functions
        import utils.config
        import data.download_guild_source
        
        # Save original functions
        self._original_get_raw_data_dir = utils.config.get_raw_data_dir
        self._original_get_metadata_file = utils.config.get_metadata_file
        
        # Override with test versions
        utils.config.get_raw_data_dir = lambda: self.raw_data_dir
        utils.config.get_metadata_file = lambda: self.metadata_file
        data.download_guild_source.get_raw_data_dir = lambda: self.raw_data_dir
        data.download_guild_source.get_metadata_file = lambda: self.metadata_file

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        
        # Restore original functions
        import utils.config
        import data.download_guild_source
        utils.config.get_raw_data_dir = self._original_get_raw_data_dir
        utils.config.get_metadata_file = self._original_get_metadata_file
        data.download_guild_source.get_raw_data_dir = self._original_get_raw_data_dir
        data.download_guild_source.get_metadata_file = self._original_get_metadata_file

    def test_validate_guild_source_valid_file(self):
        """Test validation of a valid guild source file."""
        # Create a valid CSV file
        test_file = self.raw_data_dir / "test_guilds.csv"
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['species_id', 'foraging_guild', 'source_citation'])
            writer.writerow(['A001', 'ground_forager', 'Test Citation'])
            writer.writerow(['A002', 'canopy_forager', 'Test Citation'])
        
        # Should not raise
        result = validate_guild_source(test_file)
        self.assertTrue(result)

    def test_validate_guild_source_missing_columns(self):
        """Test validation fails for missing required columns."""
        test_file = self.raw_data_dir / "invalid_guilds.csv"
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['species_id', 'other_column'])  # Missing foraging_guild
            writer.writerow(['A001', 'value'])
        
        with self.assertRaises(ValueError):
            validate_guild_source(test_file)

    def test_validate_guild_source_empty_file(self):
        """Test validation fails for empty CSV."""
        test_file = self.raw_data_dir / "empty_guilds.csv"
        test_file.write_text("")
        
        with self.assertRaises(FileNotFoundError):
            validate_guild_source(test_file)

    def test_validate_guild_source_no_data_rows(self):
        """Test validation fails for CSV with only headers."""
        test_file = self.raw_data_dir / "header_only.csv"
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['species_id', 'foraging_guild'])
        
        with self.assertRaises(ValueError):
            validate_guild_source(test_file)

    def test_compute_sha256(self):
        """Test SHA-256 computation."""
        test_file = self.raw_data_dir / "hash_test.txt"
        test_content = "test content for hashing"
        test_file.write_text(test_content)
        
        hash_result = compute_sha256(test_file)
        
        # Verify it's a valid SHA-256 hash (64 hex characters)
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))

    def test_load_metadata_config(self):
        """Test loading metadata configuration."""
        metadata = load_metadata_config()
        
        self.assertIn("sources", metadata)
        self.assertIn("artifacts", metadata)

    def test_load_metadata_config_missing_file(self):
        """Test loading metadata when file doesn't exist."""
        # Point to non-existent file
        import utils.config
        original_func = utils.config.get_metadata_file
        utils.config.get_metadata_file = lambda: Path("/nonexistent/metadata.yaml")
        
        try:
            metadata = load_metadata_config()
            self.assertIn("sources", metadata)
            self.assertIn("artifacts", metadata)
        finally:
            utils.config.get_metadata_file = original_func
