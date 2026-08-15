import os
import sys
import unittest
import tempfile
import csv
import shutil
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.generate_guild_mapping import (
    load_guild_source, validate_schema, save_mapping, 
    load_metadata, save_metadata, record_provenance_in_metadata
)
from utils.config import get_project_root

class TestGenerateGuildMapping(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        
        # Create a mock metadata file
        self.metadata_path = Path(self.temp_dir) / "metadata.yaml"
        self.metadata_path.write_text(yaml.dump({"sources": {}}))
        
        # Create a mock input file
        self.input_file = self.raw_dir / "guild_source.csv"
        self.input_file.write_text(
            "species_id,foraging_guild,other_col\n"
            "sp_001,granivore,extra_data\n"
            "sp_002,insectivore,more_data\n"
            "sp_003,frugivore,test\n"
        )
        
        # Temporarily override config paths if necessary, 
        # but since we are passing paths directly to functions in this test,
        # we rely on the functions' internal logic or pass the temp paths.
        # The functions in generate_guild_mapping use global config helpers.
        # For robust unit testing, we should ideally patch the config helpers
        # or ensure the test environment mimics the project structure.
        # However, the functions `load_guild_source` etc take Path objects.
        # We will test the logic functions directly.

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_load_guild_source_success(self):
        """Test that load_guild_source correctly parses the CSV."""
        rows = load_guild_source(self.input_file)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['species_id'], 'sp_001')
        self.assertEqual(rows[0]['foraging_guild'], 'granivore')
        self.assertIn('other_col', rows[0])

    def test_load_guild_source_missing_file(self):
        """Test that load_guild_source raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_guild_source(Path("/nonexistent/path.csv"))

    def test_load_guild_source_missing_columns(self):
        """Test that load_guild_source raises ValueError if columns missing."""
        bad_file = self.raw_dir / "bad.csv"
        bad_file.write_text("id,guild\n1,granivore\n") # Missing species_id or foraging_guild if case sensitive? 
        # The function checks for 'species_id' and 'foraging_guild' specifically.
        # Let's create a file missing 'species_id'
        bad_file.write_text("species_id,other\n1,test\n") # missing foraging_guild
        
        with self.assertRaises(ValueError):
            load_guild_source(bad_file)

    def test_validate_schema_valid(self):
        """Test schema validation on valid data."""
        valid_rows = [
            {'species_id': '1', 'foraging_guild': 'A'},
            {'species_id': '2', 'foraging_guild': 'B'}
        ]
        self.assertTrue(validate_schema(valid_rows))

    def test_validate_schema_invalid_missing_species(self):
        """Test schema validation fails if species_id is missing."""
        invalid_rows = [
            {'species_id': '', 'foraging_guild': 'A'},
            {'species_id': '2', 'foraging_guild': 'B'}
        ]
        self.assertFalse(validate_schema(invalid_rows))

    def test_validate_schema_invalid_missing_guild(self):
        """Test schema validation fails if foraging_guild is missing."""
        invalid_rows = [
            {'species_id': '1', 'foraging_guild': ''},
            {'species_id': '2', 'foraging_guild': 'B'}
        ]
        self.assertFalse(validate_schema(invalid_rows))

    def test_save_mapping_creates_file(self):
        """Test that save_mapping creates the output file with correct columns."""
        output_file = self.processed_dir / "mapping.csv"
        rows = [
            {'species_id': '1', 'foraging_guild': 'A'},
            {'species_id': '2', 'foraging_guild': 'B'}
        ]
        citation = "Test Source"
        date = "2023-01-01"
        
        save_mapping(output_file, rows, citation, date)
        
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            self.assertIn('species_id', fieldnames)
            self.assertIn('foraging_guild', fieldnames)
            self.assertIn('source_citation', fieldnames)
            self.assertIn('extraction_date', fieldnames)
            
            rows_read = list(reader)
            self.assertEqual(len(rows_read), 2)
            self.assertEqual(rows_read[0]['source_citation'], citation)
            self.assertEqual(rows_read[0]['extraction_date'], date)

    def test_record_provenance_in_metadata(self):
        """Test that provenance is recorded in metadata.yaml."""
        input_file = self.input_file
        output_file = self.processed_dir / "mapping.csv"
        # Ensure output exists first
        save_mapping(output_file, [{'species_id': '1', 'foraging_guild': 'A'}], "Cite", "2023-01-01")
        
        record_provenance_in_metadata(self.metadata_path, input_file, output_file, "Cite")
        
        with open(self.metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        
        self.assertIn('sources', metadata)
        self.assertIn('guild_mapping', metadata['sources'])
        
        record = metadata['sources']['guild_mapping']
        self.assertIn('input_file', record)
        self.assertIn('output_hash', record)
        self.assertEqual(record['source_citation'], "Cite")

if __name__ == '__main__':
    unittest.main()