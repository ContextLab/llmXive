import os
import sys
import unittest
import tempfile
import csv
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.generate_guild_mapping import (
    load_guild_source,
    validate_schema,
    save_mapping,
    main
)
from utils.config import get_data_dir, get_raw_data_dir, get_processed_dir

class TestGenerateGuildMapping(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.test_dir) / "raw"
        self.processed_dir = Path(self.test_dir) / "processed"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        
        # Create a mock metadata file
        self.metadata_path = Path(self.test_dir) / "metadata.yaml"
        with open(self.metadata_path, 'w') as f:
            f.write("provenance: {}\n")
        
        # Mock config functions temporarily
        self._original_get_raw = get_raw_data_dir
        self._original_get_processed = get_processed_dir
        
        # We can't easily mock the utils.config functions globally without side effects
        # So we will pass paths directly to functions where possible or use local logic
        
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.test_dir)
        
    def test_load_guild_source_valid(self):
        """Test loading a valid guild source CSV."""
        input_path = self.raw_dir / "guild_source.csv"
        data = [
            {"species_id": "sp1", "foraging_guild": "Insectivore", "source_citation": "Test"},
            {"species_id": "sp2", "foraging_guild": "Granivore", "source_citation": "Test"}
        ]
        
        with open(input_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
        result = load_guild_source(input_path)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['species_id'], 'sp1')
        self.assertIn('source_citation', result[0])
        
    def test_load_guild_source_missing_citation(self):
        """Test loading a guild source CSV missing the citation column."""
        input_path = self.raw_dir / "bad_guild_source.csv"
        data = [
            {"species_id": "sp1", "foraging_guild": "Insectivore"}
        ]
        
        with open(input_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
        with self.assertRaises(ValueError):
            load_guild_source(input_path)
            
    def test_validate_schema_valid(self):
        """Test schema validation on valid data."""
        rows = [
            {"species_id": "sp1", "foraging_guild": "Insectivore", "source_citation": "Test"}
        ]
        self.assertTrue(validate_schema(rows))
        
    def test_validate_schema_missing_field(self):
        """Test schema validation on data missing a required field."""
        rows = [
            {"species_id": "sp1", "foraging_guild": "Insectivore"}
        ]
        with self.assertRaises(ValueError):
            validate_schema(rows)
            
    def test_save_mapping(self):
        """Test saving the mapping to a CSV file."""
        output_path = self.processed_dir / "guild_mapping.csv"
        rows = [
            {"species_id": "sp1", "foraging_guild": "Insectivore", "source_citation": "Test"}
        ]
        extraction_date = "2023-01-01"
        
        save_mapping(output_path, rows, extraction_date)
        
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['extraction_date'], extraction_date)
        self.assertEqual(data[0]['species_id'], 'sp1')

if __name__ == '__main__':
    unittest.main()