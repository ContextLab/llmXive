"""
Unit tests for T008a: download_guild_source.py
"""
import os
import sys
import unittest
import tempfile
import shutil
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_processed_dir, get_raw_data_dir

class TestDownloadGuildSource(unittest.TestCase):
    def setUp(self):
        """Create temporary directories and mock input file."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir.mkdir()
        self.raw_dir.mkdir()
        
        # Mock top_species_ids.json
        self.top_species_file = self.processed_dir / "top_species_ids.json"
        self.top_species_data = ["species_a", "species_b", "species_c"]
        with open(self.top_species_file, "w") as f:
            json.dump(self.top_species_data, f)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def test_validate_guild_source_valid(self):
        """Test validation with valid data."""
        from data.download_guild_source import validate_guild_source
        valid_data = [{"species_id": "1", "foraging_guild": "A", "source_citation": "B"}]
        self.assertTrue(validate_guild_source(valid_data))

    def test_validate_guild_source_invalid(self):
        """Test validation with missing columns."""
        from data.download_guild_source import validate_guild_source
        invalid_data = [{"species_id": "1"}]
        self.assertFalse(validate_guild_source(invalid_data))

    def test_process_guild_source_filters_correctly(self):
        """Test that process_guild_source filters master mapping correctly."""
        from data.download_guild_source import process_guild_source
        
        top_ids = ["a", "b"]
        master = [
            {"species_id": "a", "foraging_guild": "G1", "source_citation": "S"},
            {"species_id": "c", "foraging_guild": "G2", "source_citation": "S"},
            {"species_id": "b", "foraging_guild": "G3", "source_citation": "S"}
        ]
        
        result = process_guild_source(top_ids, master)
        
        self.assertEqual(len(result), 2)
        species_ids = {r["species_id"] for r in result}
        self.assertEqual(species_ids, {"a", "b"})

    def test_process_guild_source_empty_list_raises(self):
        """Test that empty top species list raises FileNotFoundError."""
        from data.download_guild_source import process_guild_source
        with self.assertRaises(FileNotFoundError):
            process_guild_source([], [{"species_id": "a"}])

    def test_fallback_logic(self):
        """Test that hardcoded fallback contains expected keys."""
        from data.download_guild_source import TOP_25_FALLBACK_GUILDS
        self.assertIsInstance(TOP_25_FALLBACK_GUILDS, dict)
        self.assertGreater(len(TOP_25_FALLBACK_GUILDS), 0)

if __name__ == "__main__":
    unittest.main()