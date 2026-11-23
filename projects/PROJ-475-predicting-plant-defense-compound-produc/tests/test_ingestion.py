"""
Unit tests for data ingestion logic (T012).
"""
import unittest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    validate_compound_json_schema,
    fetch_compound_data,
    ensure_directories,
    update_manifest
)
from data.mock_generator import generate_mock_compound_data

class TestFetchCompoundData(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.test_dir) / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock config
        self.mock_config = {
            'verified_urls': {
                'compound': None
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('data.ingestion.get_config')
    @patch('data.ingestion.generate_mock_compound_data')
    def test_ingest_fails_on_missing_url_generates_mock(self, mock_gen, mock_get_config):
        """Test that missing URL triggers mock generation."""
        mock_get_config.return_value = self.mock_config
        mock_gen.return_value = [
            {
                "population_id": "POP001",
                "compound_name": "TestCompound",
                "concentration": 10.5
            }
        ]
        
        # Temporarily change output paths for test
        import data.ingestion
        original_raw_dir = data.ingestion.RAW_DATA_DIR
        data.ingestion.RAW_DATA_DIR = self.raw_dir
        data.ingestion.MOCK_COMPOUND_OUTPUT_PATH = self.raw_dir / "mock_compounds.json"
        
        try:
            result = fetch_compound_data()
            
            self.assertTrue(result['is_mock'])
            self.assertTrue(os.path.exists(result['path']))
            
            # Verify file content
            with open(result['path'], 'r') as f:
                data = json.load(f)
            
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            self.assertIn('population_id', data[0])
            self.assertIn('compound_name', data[0])
            self.assertIn('concentration', data[0])
            
        finally:
            data.ingestion.RAW_DATA_DIR = original_raw_dir
            data.ingestion.MOCK_COMPOUND_OUTPUT_PATH = Path("data/raw/mock_compounds.json")
    
    def test_validate_compound_json_schema_valid(self):
        """Test validation with valid compound data."""
        valid_data = [
            {
                "population_id": "POP001",
                "compound_name": "TestCompound",
                "concentration": 10.5
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_data, f)
            temp_path = f.name
        
        try:
            self.assertTrue(validate_compound_json_schema(temp_path))
        finally:
            os.unlink(temp_path)
    
    def test_validate_compound_json_schema_missing_keys(self):
        """Test validation with missing required keys."""
        invalid_data = [
            {
                "population_id": "POP001",
                "compound_name": "TestCompound"
                # Missing concentration
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_path = f.name
        
        try:
            self.assertFalse(validate_compound_json_schema(temp_path))
        finally:
            os.unlink(temp_path)
    
    def test_validate_compound_json_schema_empty_file(self):
        """Test validation with empty list."""
        empty_data = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_data, f)
            temp_path = f.name
        
        try:
            self.assertFalse(validate_compound_json_schema(temp_path))
        finally:
            os.unlink(temp_path)
    
    def test_validate_compound_json_schema_invalid_json(self):
        """Test validation with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name
        
        try:
            self.assertFalse(validate_compound_json_schema(temp_path))
        finally:
            os.unlink(temp_path)

class TestIngestionIntegration(unittest.TestCase):
    
    def test_mock_data_generation(self):
        """Test that mock data generator produces valid structure."""
        mock_data = generate_mock_compound_data()
        
        self.assertIsInstance(mock_data, list)
        self.assertGreater(len(mock_data), 0)
        
        for record in mock_data:
            self.assertIn('population_id', record)
            self.assertIn('compound_name', record)
            self.assertIn('concentration', record)
            self.assertIsInstance(record['population_id'], str)
            self.assertIsInstance(record['compound_name'], str)
            self.assertIsInstance(record['concentration'], (int, float))

if __name__ == '__main__':
    unittest.main()