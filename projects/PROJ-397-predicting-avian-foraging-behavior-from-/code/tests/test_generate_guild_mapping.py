"""
Unit tests for data/generate_guild_mapping.py
"""

import os
import sys
import unittest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.generate_guild_mapping import (
    validate_schema, 
    save_mapping, 
    fetch_guild_mapping,
    load_metadata
)
from utils.config import get_project_root

class TestGenerateGuildMapping(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = [
            {'species_id': 'Turdus_migratorius', 'foraging_guild': 'Ground_forager'},
            {'species_id': 'Cardinalis_cardinalis', 'foraging_guild': 'Seed_eater'},
            {'species_id': 'Accipiter_strigatus', 'foraging_guild': 'Aerial_hunter'}
        ]
        
    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        self.assertTrue(validate_schema(self.test_data))
        
    def test_validate_schema_empty(self):
        """Test schema validation with empty data."""
        self.assertFalse(validate_schema([]))
        
    def test_validate_schema_missing_fields(self):
        """Test schema validation with missing required fields."""
        invalid_data = [{'species_id': 'Test'}]  # Missing foraging_guild
        self.assertFalse(validate_schema(invalid_data))
        
    def test_save_mapping_creates_file(self):
        """Test that save_mapping creates the output file with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_mapping.csv'
            save_mapping(self.test_data, output_path)
            
            self.assertTrue(output_path.exists())
            
            # Read and verify content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            # Check required columns exist
            self.assertIn('species_id', rows[0])
            self.assertIn('foraging_guild', rows[0])
            self.assertIn('source_citation', rows[0])
            self.assertIn('extraction_date', rows[0])
            
            # Check data integrity
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]['species_id'], 'Turdus_migratorius')
            self.assertEqual(rows[0]['foraging_guild'], 'Ground_forager')

    @patch('data.generate_guild_mapping.requests.get')
    def test_fetch_guild_mapping_success(self, mock_get):
        """Test successful fetch from source URL."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = """species_id,foraging_guild
        Turdus_migratorius,Ground_forager
        Cardinalis_cardinalis,Seed_eater"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = fetch_guild_mapping("http://example.com/guilds.csv")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['species_id'], 'Turdus_migratorius')
        self.assertEqual(result[0]['foraging_guild'], 'Ground_forager')

    @patch('data.generate_guild_mapping.requests.get')
    def test_fetch_guild_mapping_failure(self, mock_get):
        """Test fetch raises error on failure."""
        mock_get.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception):
            fetch_guild_mapping("http://example.com/guilds.csv")

    def test_load_metadata_missing_file(self):
        """Test that load_metadata raises error when metadata file is missing."""
        # Temporarily rename metadata file if it exists
        metadata_path = get_project_root() / 'data' / 'metadata.yaml'
        original_exists = metadata_path.exists()
        
        if original_exists:
            temp_path = metadata_path.with_suffix('.yaml.bak')
            metadata_path.rename(temp_path)
        
        try:
            with self.assertRaises(FileNotFoundError):
                load_metadata()
        finally:
            # Restore original file
            if original_exists:
                temp_path.rename(metadata_path)

if __name__ == '__main__':
    unittest.main()