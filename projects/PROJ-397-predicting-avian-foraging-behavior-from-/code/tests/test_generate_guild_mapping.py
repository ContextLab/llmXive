"""
Unit tests for T008b: generate_guild_mapping.py
"""
import os
import sys
import unittest
import tempfile
import csv
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_guild_mapping import (
    load_guild_source,
    validate_schema,
    save_mapping,
    REQUIRED_COLUMNS
)

class TestGenerateGuildMapping(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.input_path = Path(self.test_dir) / "guild_source.csv"
        self.output_path = Path(self.test_dir) / "guild_mapping.csv"
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_load_guild_source_valid(self):
        """Test loading a valid guild source CSV."""
        # Create valid input
        with open(self.input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'species_id': 'sp_001',
                'foraging_guild': 'insectivore',
                'source_citation': 'Birds of the World'
            })
        
        rows = load_guild_source(self.input_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['species_id'], 'sp_001')
        self.assertEqual(rows[0]['foraging_guild'], 'insectivore')
    
    def test_load_guild_source_missing_columns(self):
        """Test that missing columns raise ValueError."""
        with open(self.input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['species_id', 'foraging_guild'])
            writer.writeheader()
            writer.writerow({'species_id': 'sp_001', 'foraging_guild': 'insectivore'})
        
        with self.assertRaises(ValueError) as context:
            load_guild_source(self.input_path)
        self.assertIn('source_citation', str(context.exception))
    
    def test_load_guild_source_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_guild_source(Path(self.test_dir) / "nonexistent.csv")
    
    def test_validate_schema_valid(self):
        """Test validation of valid data."""
        rows = [
            {'species_id': 'sp_001', 'foraging_guild': 'insectivore', 'source_citation': 'BoW'},
            {'species_id': 'sp_002', 'foraging_guild': 'granivore', 'source_citation': 'BoW'}
        ]
        valid_rows = validate_schema(rows)
        self.assertEqual(len(valid_rows), 2)
    
    def test_validate_schema_missing_species_id(self):
        """Test validation rejects empty species_id."""
        rows = [
            {'species_id': '', 'foraging_guild': 'insectivore', 'source_citation': 'BoW'},
            {'species_id': 'sp_002', 'foraging_guild': 'granivore', 'source_citation': 'BoW'}
        ]
        valid_rows = validate_schema(rows)
        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(valid_rows[0]['species_id'], 'sp_002')
    
    def test_validate_schema_missing_guild(self):
        """Test validation handles missing guild gracefully (logs warning, keeps row)."""
        rows = [
            {'species_id': 'sp_001', 'foraging_guild': '', 'source_citation': 'BoW'},
            {'species_id': 'sp_002', 'foraging_guild': 'granivore', 'source_citation': 'BoW'}
        ]
        valid_rows = validate_schema(rows)
        # Empty guild results in row being set to None and removed
        self.assertEqual(len(valid_rows), 1)
    
    def test_save_mapping_creates_file(self):
        """Test that save_mapping creates the output file."""
        rows = [
            {'species_id': 'sp_001', 'foraging_guild': 'insectivore', 'source_citation': 'BoW'}
        ]
        save_mapping(rows, self.output_path)
        
        self.assertTrue(self.output_path.exists())
        
        with open(self.output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows_out = list(reader)
        
        self.assertEqual(len(rows_out), 1)
        self.assertEqual(rows_out[0]['species_id'], 'sp_001')
        self.assertIn('extraction_date', rows_out[0])
    
    def test_save_mapping_columns(self):
        """Test that output file has correct columns."""
        rows = [
            {'species_id': 'sp_001', 'foraging_guild': 'insectivore', 'source_citation': 'BoW'}
        ]
        save_mapping(rows, self.output_path)
        
        with open(self.output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.assertEqual(set(reader.fieldnames), {'species_id', 'foraging_guild', 'source_citation', 'extraction_date'})

if __name__ == '__main__':
    unittest.main()