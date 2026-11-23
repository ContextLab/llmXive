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

# We need to add the code directory to the path to import utils
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from data.generate_guild_mapping import (
    load_guild_source,
    validate_schema,
    save_mapping,
    get_input_file_path,
    get_output_file_path
)

class TestGenerateGuildMapping(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.test_dir) / "raw"
        self.processed_dir = Path(self.test_dir) / "processed"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        
        # Patch the config functions temporarily
        self.original_get_raw = None
        self.original_get_processed = None
        
        # We will use direct path arguments in tests instead of mocking config
        # to avoid complex patching of utils.config

    def tearDown(self):
        """Remove temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_load_guild_source_file_not_found(self):
        """Test that FileNotFoundError is raised when input is missing."""
        non_existent_path = Path(self.test_dir) / "non_existent.csv"
        with self.assertRaises(FileNotFoundError):
            load_guild_source(non_existent_path)

    def test_load_guild_source_success(self):
        """Test successful loading of a valid CSV."""
        input_path = self.raw_dir / "guild_source.csv"
        data = [
            {"species_id": "123", "foraging_guild": "Ground", "source_citation": "Test Ref"},
            {"species_id": "456", "foraging_guild": "Canopy", "source_citation": "Test Ref 2"}
        ]
        
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["species_id", "foraging_guild", "source_citation"])
            writer.writeheader()
            writer.writerows(data)
        
        loaded = load_guild_source(input_path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]['species_id'], '123')

    def test_load_guild_source_missing_columns(self):
        """Test that ValueError is raised if columns are missing."""
        input_path = self.raw_dir / "bad_guild_source.csv"
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["species_id", "wrong_col"])
            writer.writeheader()
            writer.writerow({"species_id": "123", "wrong_col": "val"})
        
        with self.assertRaises(ValueError):
            load_guild_source(input_path)

    def test_validate_schema_empty_data(self):
        """Test validation on empty data."""
        with self.assertRaises(ValueError):
            validate_schema([])

    def test_validate_schema_missing_field(self):
        """Test validation on data with missing required field."""
        data = [{"species_id": "123", "foraging_guild": "Ground"}] # Missing citation
        with self.assertRaises(ValueError):
            validate_schema(data)

    def test_validate_schema_valid(self):
        """Test validation on valid data."""
        data = [
            {"species_id": "123", "foraging_guild": "Ground", "source_citation": "Ref"},
            {"species_id": "456", "foraging_guild": "Canopy", "source_citation": "Ref"}
        ]
        self.assertTrue(validate_schema(data))

    def test_save_mapping_creates_file(self):
        """Test that save_mapping creates the output file correctly."""
        output_path = self.processed_dir / "guild_mapping.csv"
        data = [
            {"species_id": "123", "foraging_guild": "Ground", "source_citation": "Ref"}
        ]
        
        save_mapping(data, output_path)
        
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertIn('extraction_date', rows[0])
        self.assertEqual(rows[0]['species_id'], '123')

    def test_save_mapping_directory_creation(self):
        """Test that save_mapping creates parent directories if missing."""
        deep_path = self.processed_dir / "sub" / "deep" / "mapping.csv"
        data = [{"species_id": "123", "foraging_guild": "Ground", "source_citation": "Ref"}]
        
        save_mapping(data, deep_path)
        
        self.assertTrue(deep_path.exists())
