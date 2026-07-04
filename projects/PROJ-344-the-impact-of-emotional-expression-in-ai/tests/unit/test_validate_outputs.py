"""
Unit tests for T028: validate_outputs.py
Tests validation logic for CSV, JSON, and PNG artifacts.
"""
import os
import sys
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate_outputs import (
    validate_csv_schema,
    validate_json_schema,
    validate_png_file,
    validate_success_criteria
)
from config import PROJECT_ROOT

class TestValidateOutputs(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.temp_dir, "test.csv")
        self.test_json_path = os.path.join(self.temp_dir, "test.json")
        self.test_png_path = os.path.join(self.temp_dir, "test.png")
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_csv_schema_empty_file(self):
        """Test validation fails for empty CSV file."""
        # Create empty file
        with open(self.test_csv_path, 'w') as f:
            pass
        
        result = validate_csv_schema(self.test_csv_path, "dummy_schema.yaml")
        self.assertFalse(result)
    
    def test_validate_csv_schema_missing_columns(self):
        """Test validation fails when required columns are missing."""
        # Create CSV with missing columns
        with open(self.test_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'value'])
            writer.writeheader()
            writer.writerow({'id': '1', 'value': '10'})
        
        # Mock schema with required columns
        mock_schema = {
            'required_columns': ['id', 'consistency_score', 'trust_score']
        }
        
        with patch('validate_outputs.load_schema', return_value=mock_schema):
            result = validate_csv_schema(self.test_csv_path, "dummy_schema.yaml")
            self.assertFalse(result)
    
    def test_validate_csv_schema_valid(self):
        """Test validation passes for valid CSV with correct columns and values."""
        # Create valid CSV
        with open(self.test_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['interaction_id', 'consistency_score', 'trust_score'])
            writer.writeheader()
            writer.writerow({'interaction_id': '001', 'consistency_score': '0.75', 'trust_score': '85.0'})
            writer.writerow({'interaction_id': '002', 'consistency_score': '0.42', 'trust_score': '72.5'})
        
        mock_schema = {
            'required_columns': ['interaction_id', 'consistency_score', 'trust_score']
        }
        
        with patch('validate_outputs.load_schema', return_value=mock_schema):
            result = validate_csv_schema(self.test_csv_path, "dummy_schema.yaml")
            self.assertTrue(result)
    
    def test_validate_csv_schema_invalid_consistency_score(self):
        """Test validation fails for out-of-range consistency score."""
        with open(self.test_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['interaction_id', 'consistency_score', 'trust_score'])
            writer.writeheader()
            writer.writerow({'interaction_id': '001', 'consistency_score': '1.5', 'trust_score': '85.0'})
        
        mock_schema = {
            'required_columns': ['interaction_id', 'consistency_score', 'trust_score']
        }
        
        with patch('validate_outputs.load_schema', return_value=mock_schema):
            result = validate_csv_schema(self.test_csv_path, "dummy_schema.yaml")
            self.assertFalse(result)
    
    def test_validate_json_schema_invalid_format(self):
        """Test validation fails for invalid JSON format."""
        with open(self.test_json_path, 'w') as f:
            f.write("not valid json")
        
        result = validate_json_schema(self.test_json_path, "dummy_schema.yaml")
        self.assertFalse(result)
    
    def test_validate_json_schema_missing_keys(self):
        """Test validation fails when required keys are missing."""
        data = {'some_key': 'value'}
        with open(self.test_json_path, 'w') as f:
            json.dump(data, f)
        
        mock_schema = {
            'required_keys': ['correlation_coefficient', 'confidence_interval', 'p_value']
        }
        
        with patch('validate_outputs.load_schema', return_value=mock_schema):
            result = validate_json_schema(self.test_json_path, "dummy_schema.yaml")
            self.assertFalse(result)
    
    def test_validate_json_schema_valid(self):
        """Test validation passes for valid JSON with all required fields."""
        data = {
            'correlation_coefficient': 0.75,
            'confidence_interval': [0.65, 0.85],
            'p_value': 0.001,
            'sample_size': 500
        }
        with open(self.test_json_path, 'w') as f:
            json.dump(data, f)
        
        mock_schema = {
            'required_keys': ['correlation_coefficient', 'confidence_interval', 'p_value']
        }
        
        with patch('validate_outputs.load_schema', return_value=mock_schema):
            result = validate_json_schema(self.test_json_path, "dummy_schema.yaml")
            self.assertTrue(result)
    
    def test_validate_png_file_missing(self):
        """Test validation fails for missing PNG file."""
        result = validate_png_file("/nonexistent/path/test.png")
        self.assertFalse(result)
    
    def test_validate_png_file_empty(self):
        """Test validation fails for empty PNG file."""
        with open(self.test_png_path, 'w') as f:
            pass
        
        result = validate_png_file(self.test_png_path)
        self.assertFalse(result)
    
    def test_validate_png_file_invalid_signature(self):
        """Test validation fails for PNG with invalid signature."""
        with open(self.test_png_path, 'wb') as f:
            f.write(b"NOT A PNG FILE")
        
        result = validate_png_file(self.test_png_path)
        self.assertFalse(result)
    
    def test_validate_png_file_valid(self):
        """Test validation passes for valid PNG file."""
        # Create a minimal valid PNG (1x1 pixel)
        png_data = (
            b'\x89PNG\r\n\x1a\n'  # Signature
            b'\x00\x00\x00\rIHDR'  # IHDR chunk length + type
            b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'  # IHDR data + CRC
            b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'  # IDAT data
            b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
        )
        with open(self.test_png_path, 'wb') as f:
            f.write(png_data)
        
        result = validate_png_file(self.test_png_path)
        self.assertTrue(result)
    
    def test_validate_png_file_zero_dimensions(self):
        """Test validation fails for PNG with zero dimensions."""
        # Create PNG with 0x0 dimensions in IHDR
        png_data = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\x02\x00\x00\x00\x00\x00\x00'  # 0x0 dimensions
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        with open(self.test_png_path, 'wb') as f:
            f.write(png_data)
        
        result = validate_png_file(self.test_png_path)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
