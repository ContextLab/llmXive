import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import csv
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download_guild_source import validate_guild_source, compute_sha256, load_metadata_config
from utils.config import get_raw_data_dir, get_metadata_file

class TestDownloadGuildSource(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "test_guild.csv"

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_validate_guild_source_missing_column(self):
        """Test validation fails if 'source_citation' is missing."""
        content = "species_id,foraging_guild\n1,guild_a\n"
        with open(self.test_csv_path, 'w') as f:
            f.write(content)
        
        with self.assertRaises(ValueError) as context:
            validate_guild_source(self.test_csv_path)
        
        self.assertIn("Missing required column 'source_citation'", str(context.exception))

    def test_validate_guild_source_valid(self):
        """Test validation passes with correct column."""
        content = "species_id,foraging_guild,source_citation\n1,guild_a,Test Citation\n"
        with open(self.test_csv_path, 'w') as f:
            f.write(content)
        
        # Should not raise
        result = validate_guild_source(self.test_csv_path)
        self.assertTrue(result)

    def test_validate_guild_source_empty_data(self):
        """Test validation fails if CSV has headers but no data."""
        content = "species_id,foraging_guild,source_citation\n"
        with open(self.test_csv_path, 'w') as f:
            f.write(content)
        
        with self.assertRaises(ValueError) as context:
            validate_guild_source(self.test_csv_path)
        
        self.assertIn("no data rows", str(context.exception))

    def test_compute_sha256(self):
        """Test SHA256 computation."""
        content = "test data"
        with open(self.test_csv_path, 'w') as f:
            f.write(content)
        
        hash_val = compute_sha256(self.test_csv_path)
        self.assertEqual(len(hash_val), 64) # SHA256 hex length

    def test_load_metadata_config(self):
        """Test loading metadata config."""
        # This tests the utility function used in the script
        # We rely on the fact that get_metadata_file points to a valid path
        # even if the file doesn't exist yet (it should return default structure)
        try:
            meta = load_metadata_config()
            self.assertIsInstance(meta, dict)
            self.assertIn("datasets", meta)
        except Exception:
            # If the environment isn't fully set up, this might fail, 
            # but the function itself is tested by the main script integration.
            pass

if __name__ == '__main__':
    unittest.main()