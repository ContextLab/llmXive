import os
import sys
import unittest
import tempfile
import csv
import shutil
from pathlib import Path
from datetime import datetime
import yaml

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.generate_guild_mapping import (
    load_guild_source,
    validate_schema,
    save_mapping,
    record_provenance_in_metadata,
    load_metadata,
    save_metadata
)
from utils.config import get_data_dir, get_raw_data_dir, get_processed_dir

class TestGenerateGuildMapping(unittest.TestCase):
    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.data_dir = Path(self.temp_dir)
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        
        # Create a mock source file
        self.mock_source = self.raw_dir / "guild_source.csv"
        with open(self.mock_source, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['species_id', 'foraging_guild', 'extra_col'])
            writer.writerow(['12345', 'Granivore', 'extra_data'])
            writer.writerow(['67890', 'Insectivore', 'more_data'])
            writer.writerow(['11111', 'Nectarivore', 'data'])

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def test_load_guild_source_valid(self):
        """Test loading a valid guild source CSV."""
        data = load_guild_source(self.mock_source)
        self.assertEqual(len(data), 3)
        self.assertIn('species_id', data[0])
        self.assertIn('foraging_guild', data[0])
        self.assertEqual(data[0]['species_id'], '12345')
        self.assertEqual(data[0]['foraging_guild'], 'Granivore')

    def test_load_guild_source_missing_file(self):
        """Test loading a non-existent guild source raises error."""
        non_existent = self.raw_dir / "non_existent.csv"
        with self.assertRaises(FileNotFoundError):
            load_guild_source(non_existent)

    def test_load_guild_source_missing_columns(self):
        """Test loading a source with missing required columns raises error."""
        bad_source = self.raw_dir / "bad_source.csv"
        with open(bad_source, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['species_id', 'other_col']) # Missing foraging_guild
            writer.writerow(['12345', 'val'])
        
        with self.assertRaises(ValueError):
            load_guild_source(bad_source)

    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        valid_data = [
            {'species_id': '1', 'foraging_guild': 'G', 'source_citation': 'C', 'extraction_date': '2023-01-01'},
            {'species_id': '2', 'foraging_guild': 'I', 'source_citation': 'C', 'extraction_date': '2023-01-01'}
        ]
        result = validate_schema(valid_data)
        self.assertTrue(result)

    def test_validate_schema_empty(self):
        """Test schema validation with empty data."""
        with self.assertRaises(ValueError):
            validate_schema([])

    def test_validate_schema_missing_keys(self):
        """Test schema validation with missing keys."""
        bad_data = [
            {'species_id': '1', 'foraging_guild': 'G'} # Missing citation and date
        ]
        with self.assertRaises(ValueError):
            validate_schema(bad_data)

    def test_save_mapping(self):
        """Test saving mapping to CSV."""
        output_path = self.processed_dir / "test_mapping.csv"
        data = [
            {'species_id': '1', 'foraging_guild': 'G', 'source_citation': 'C', 'extraction_date': '2023-01-01'},
            {'species_id': '2', 'foraging_guild': 'I', 'source_citation': 'C', 'extraction_date': '2023-01-01'}
        ]
        
        save_mapping(data, output_path)
        
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['species_id'], '1')
        self.assertEqual(rows[0]['foraging_guild'], 'G')
        self.assertEqual(rows[0]['source_citation'], 'C')
        self.assertEqual(rows[0]['extraction_date'], '2023-01-01')

    def test_record_provenance_in_metadata(self):
        """Test recording provenance in metadata."""
        # Create a dummy output file first
        output_path = self.processed_dir / "dummy_output.csv"
        with open(output_path, 'w') as f:
            f.write("species_id,foraging_guild\n1,G\n")
        
        metadata = {}
        updated_metadata = record_provenance_in_metadata(metadata, self.mock_source, output_path)
        
        self.assertIn('steps', updated_metadata)
        self.assertEqual(len(updated_metadata['steps']), 1)
        
        step = updated_metadata['steps'][0]
        self.assertEqual(step['step'], 'generate_guild_mapping')
        self.assertEqual(step['input_file'], str(self.mock_source))
        self.assertEqual(step['output_file'], str(output_path))
        self.assertIn('input_hash', step)
        self.assertIn('output_hash', step)
        self.assertEqual(step['row_count'], 1) # 1 data row + 1 header

    def test_load_and_save_metadata(self):
        """Test loading and saving metadata YAML."""
        metadata_path = self.data_dir / "test_metadata.yaml"
        test_data = {'key': 'value', 'nested': {'a': 1}}
        
        save_metadata(test_data, metadata_path)
        self.assertTrue(metadata_path.exists())
        
        loaded = load_metadata(metadata_path)
        self.assertEqual(loaded['key'], 'value')
        self.assertEqual(loaded['nested']['a'], 1)

if __name__ == '__main__':
    unittest.main()