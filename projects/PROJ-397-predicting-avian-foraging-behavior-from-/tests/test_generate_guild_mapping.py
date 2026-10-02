"""
Unit tests for T008b: generate_guild_mapping.py
"""
import os
import sys
import unittest
import tempfile
import shutil
import csv
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
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
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "data" / "raw"
        self.processed_dir = Path(self.temp_dir) / "data" / "processed"
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        
        # Mock config to use temp dirs if necessary, 
        # but usually we test functions that take paths directly.
        # For get_input_file_path/get_output_file_path, we rely on utils.config.
        # To avoid mocking the whole config system, we will test the core logic functions
        # with explicit paths in the temp dir.

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_guild_source_valid(self):
        """Test loading a valid CSV file."""
        input_file = self.raw_dir / "guild_source.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['species_id', 'foraging_guild', 'source_citation'])
            writer.writeheader()
            writer.writerow({'species_id': '1', 'foraging_guild': 'A', 'source_citation': 'Test'})
        
        rows = load_guild_source(input_file)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['species_id'], '1')

    def test_load_guild_source_empty(self):
        """Test loading an empty CSV (header only)."""
        input_file = self.raw_dir / "empty_source.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['species_id', 'foraging_guild', 'source_citation'])
            writer.writeheader()
        
        with self.assertRaises(ValueError):
            load_guild_source(input_file)

    def test_validate_schema_missing_columns(self):
        """Test validation fails on missing columns."""
        rows = [{'species_id': '1', 'foraging_guild': 'A'}] # Missing source_citation
        with self.assertRaises(ValueError):
            validate_schema(rows, Path("dummy"))

    def test_validate_schema_valid(self):
        """Test validation passes on valid data."""
        rows = [
            {'species_id': '1', 'foraging_guild': 'A', 'source_citation': 'C'},
            {'species_id': '2', 'foraging_guild': 'B', 'source_citation': 'C'}
        ]
        try:
            validate_schema(rows, Path("dummy"))
        except ValueError:
            self.fail("validate_schema raised ValueError unexpectedly")

    def test_save_mapping_creates_file(self):
        """Test that save_mapping creates the output file with correct content."""
        rows = [
            {'species_id': '1', 'foraging_guild': 'A', 'source_citation': 'C'},
            {'species_id': '2', 'foraging_guild': 'B', 'source_citation': 'C'}
        ]
        output_file = self.processed_dir / "guild_mapping.csv"
        date_str = "2023-01-01"
        
        save_mapping(rows, output_file, date_str)
        
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        self.assertEqual(len(data), 2)
        self.assertIn('extraction_date', data[0])
        self.assertEqual(data[0]['extraction_date'], date_str)
        self.assertEqual(data[0]['species_id'], '1')

    def test_save_mapping_empty_rows(self):
        """Test saving empty rows raises error or handles gracefully."""
        output_file = self.processed_dir / "empty_mapping.csv"
        with self.assertRaises(ValueError):
            save_mapping([], output_file, "2023-01-01")

if __name__ == '__main__':
    unittest.main()