import os
import sys
import unittest
import tempfile
import shutil
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download_guild_source import get_input_file_path, get_output_file_path, process_guild_source, validate_guild_source

class TestDownloadGuildSource(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Mock the config to use temp dirs
        import utils.config
        self.original_get_processed_dir = utils.config.get_processed_dir
        self.original_get_raw_data_dir = utils.config.get_raw_data_dir
        
        utils.config.get_processed_dir = lambda: Path(self.temp_dir)
        utils.config.get_raw_data_dir = lambda: Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        utils.config.get_processed_dir = self.original_get_processed_dir
        utils.config.get_raw_data_dir = self.original_get_raw_data_dir

    def test_process_guild_source_filters_correctly(self):
        full_mapping = [
            {"species_id": "A", "foraging_guild": "G1", "source_citation": "C1"},
            {"species_id": "B", "foraging_guild": "G2", "source_citation": "C2"},
            {"species_id": "C", "foraging_guild": "G3", "source_citation": "C3"},
        ]
        top_species = ["A", "C"]
        result = process_guild_source(full_mapping, top_species)
        self.assertEqual(len(result), 2)
        ids = [r["species_id"] for r in result]
        self.assertIn("A", ids)
        self.assertIn("C", ids)
        self.assertNotIn("B", ids)

    def test_validate_guild_source_empty(self):
        self.assertFalse(validate_guild_source([]))

    def test_validate_guild_source_missing_key(self):
        data = [{"species_id": "A", "foraging_guild": "G1"}] # missing source_citation
        self.assertFalse(validate_guild_source(data))

    def test_validate_guild_source_valid(self):
        data = [{"species_id": "A", "foraging_guild": "G1", "source_citation": "C1"}]
        self.assertTrue(validate_guild_source(data))

    def test_file_paths(self):
        # Ensure paths are constructed correctly relative to temp dir
        input_p = get_input_file_path()
        output_p = get_output_file_path()
        self.assertTrue(str(input_p).endswith("top_species_ids.json"))
        self.assertTrue(str(output_p).endswith("guild_mapping_manual.csv"))

if __name__ == "__main__":
    unittest.main()