import os
import sys
import unittest
import tempfile
import csv
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path if not already there
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.generate_guild_mapping import (
    load_guild_source,
    validate_schema,
    save_mapping,
    get_input_file_path,
    get_output_file_path
)
from utils.config import get_raw_data_dir, get_processed_dir

class TestGenerateGuildMapping(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        
        # Mock config functions temporarily if needed, 
        # but for this test we will pass explicit paths to functions 
        # or rely on the fact that we are testing logic not path resolution.
        # Since the module uses get_raw_data_dir(), we need to ensure 
        # the test environment matches or we test the logic directly.
        
        # Create a mock input file
        self.mock_input_path = self.raw_dir / "guild_source.csv"
        self.mock_output_path = self.processed_dir / "guild_mapping.csv"
        
        mock_data = [
            {"species_id": "sp001", "foraging_guild": "ground", "source_citation": "Ref A"},
            {"species_id": "sp002", "foraging_guild": "canopy", "source_citation": "Ref B"},
            {"species_id": "sp003", "foraging_guild": "aerial", "source_citation": "Ref C"}
        ]
        
        with open(self.mock_input_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["species_id", "foraging_guild", "source_citation"])
            writer.writeheader()
            writer.writerows(mock_data)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def test_load_guild_source(self):
        """Test loading the guild source CSV."""
        records = load_guild_source(self.mock_input_path)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]['species_id'], 'sp001')
        self.assertEqual(records[0]['foraging_guild'], 'ground')

    def test_load_guild_source_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_guild_source(Path("/nonexistent/path.csv"))

    def test_validate_schema_valid(self):
        """Test validation with valid data."""
        records = [
            {"species_id": "s1", "foraging_guild": "g1", "source_citation": "c1"},
            {"species_id": "s2", "foraging_guild": "g2", "source_citation": "c2"}
        ]
        self.assertTrue(validate_schema(records))

    def test_validate_schema_missing_species_id(self):
        """Test validation fails with missing species_id."""
        records = [
            {"foraging_guild": "g1", "source_citation": "c1"}
        ]
        with self.assertRaises(ValueError):
            validate_schema(records)

    def test_validate_schema_missing_guild(self):
        """Test validation fails with missing foraging_guild."""
        records = [
            {"species_id": "s1", "source_citation": "c1"}
        ]
        with self.assertRaises(ValueError):
            validate_schema(records)

    def test_save_mapping(self):
        """Test saving the mapping to CSV."""
        records = [
            {"species_id": "s1", "foraging_guild": "g1", "source_citation": "c1"}
        ]
        save_mapping(records, self.mock_output_path)
        
        self.assertTrue(self.mock_output_path.exists())
        
        with open(self.mock_output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['species_id'], 's1')
        self.assertIn('extraction_date', rows[0])
        self.assertIn('foraging_guild', rows[0])
        self.assertIn('source_citation', rows[0])

    def test_save_mapping_creates_directory(self):
        """Test that save_mapping creates the output directory if it doesn't exist."""
        new_dir = Path(self.temp_dir) / "new_processed"
        new_output_path = new_dir / "test.csv"
        
        records = [
            {"species_id": "s1", "foraging_guild": "g1", "source_citation": "c1"}
        ]
        save_mapping(records, new_output_path)
        
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_output_path.exists())

if __name__ == '__main__':
    unittest.main()