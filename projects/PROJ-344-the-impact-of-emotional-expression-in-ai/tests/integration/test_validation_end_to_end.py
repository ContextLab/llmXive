"""
Integration test for T028: End-to-end validation of all output artifacts.
This test simulates the full validation pipeline with mock data.
"""
import os
import sys
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate_outputs import validate_success_criteria

class TestValidationEndToEnd(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary test files."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock CSV
        self.mock_csv = os.path.join(self.temp_dir, "consistency_results.csv")
        with open(self.mock_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['interaction_id', 'consistency_score', 'trust_score'])
            writer.writeheader()
            writer.writerow({'interaction_id': '001', 'consistency_score': '0.75', 'trust_score': '85.0'})
            writer.writerow({'interaction_id': '002', 'consistency_score': '0.42', 'trust_score': '72.5'})
        
        # Create mock JSON
        self.mock_json = os.path.join(self.temp_dir, "analysis_results.json")
        with open(self.mock_json, 'w') as f:
            json.dump({
                'correlation_coefficient': 0.68,
                'confidence_interval': [0.55, 0.81],
                'p_value': 0.0003,
                'sample_size': 500
            }, f)
        
        # Create mock PNG
        self.mock_png = os.path.join(self.temp_dir, "scatter_plot.png")
        png_data = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR'
            b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        with open(self.mock_png, 'wb') as f:
            f.write(png_data)
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('validate_outputs.OUTPUT_CSV_PATH')
    @patch('validate_outputs.OUTPUT_JSON_PATH')
    @patch('validate_outputs.OUTPUT_PNG_PATH')
    @patch('validate_outputs.SCHEMA_PATH_DATASET')
    @patch('validate_outputs.SCHEMA_PATH_FEATURES')
    def test_all_valid_artifacts(
        self, mock_schema_feat, mock_schema_data, mock_png, mock_json, mock_csv
    ):
        """Test validation passes when all artifacts are valid."""
        mock_csv.return_value = self.mock_csv
        mock_json.return_value = self.mock_json
        mock_png.return_value = self.mock_png
        mock_schema_data.return_value = "dummy_schema.yaml"
        mock_schema_feat.return_value = "dummy_schema.yaml"
        
        # Mock load_schema to return valid schemas
        mock_schema_data_content = {'required_columns': ['interaction_id', 'consistency_score', 'trust_score']}
        mock_schema_feat_content = {'required_keys': ['correlation_coefficient', 'confidence_interval', 'p_value']}
        
        with patch('validate_outputs.load_schema') as mock_load:
            mock_load.side_effect = [mock_schema_data_content, mock_schema_feat_content]
            
            all_valid, failures = validate_success_criteria()
            
            self.assertTrue(all_valid)
            self.assertEqual(len(failures), 0)
    
    @patch('validate_outputs.OUTPUT_CSV_PATH')
    @patch('validate_outputs.OUTPUT_JSON_PATH')
    @patch('validate_outputs.OUTPUT_PNG_PATH')
    def test_missing_csv_artifact(self, mock_png, mock_json, mock_csv):
        """Test validation fails when CSV is missing."""
        mock_csv.return_value = "/nonexistent/path.csv"
        mock_json.return_value = self.mock_json
        mock_png.return_value = self.mock_png
        
        all_valid, failures = validate_success_criteria()
        
        self.assertFalse(all_valid)
        self.assertTrue(any("CSV" in f for f in failures))
    
    @patch('validate_outputs.OUTPUT_CSV_PATH')
    @patch('validate_outputs.OUTPUT_JSON_PATH')
    @patch('validate_outputs.OUTPUT_PNG_PATH')
    def test_invalid_png_artifact(self, mock_png, mock_json, mock_csv):
        """Test validation fails when PNG is invalid."""
        mock_csv.return_value = self.mock_csv
        mock_json.return_value = self.mock_json
        mock_png.return_value = "/nonexistent/invalid.png"
        
        all_valid, failures = validate_success_criteria()
        
        self.assertFalse(all_valid)
        self.assertTrue(any("PNG" in f for f in failures))

if __name__ == '__main__':
    unittest.main()
