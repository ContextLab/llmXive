"""Unit tests for ingestion logic in code/data/ingestion.py.

This module tests the ingestion functions with mocked downloads to ensure
they correctly handle URL fetching, parsing, and saving data without
requiring actual network access or API keys.
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    fetch_url_content,
    parse_compound_data,
    fetch_compound_data,
    save_data,
    run_all_ingestion
)
from data.mock_generator import (
    generate_mock_genomic_data,
    generate_mock_environmental_data,
    generate_mock_compound_data
)
from config import get_config, load_config, reset_config
from utils.logging import get_module_logger

class TestIngestion(unittest.TestCase):
    """Test cases for ingestion logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir()
        
        # Reset config to ensure clean state
        reset_config()
        
        # Create a minimal config for testing
        self.config_path = Path(self.test_dir) / "config.yaml"
        with open(self.config_path, 'w') as f:
            f.write("""
            paths:
              raw_data: data/raw
              processed_data: data/processed
            verified_urls:
              genomic: null
              env: null
              compound: null
            """)
        
        load_config(self.config_path)
        self.logger = get_module_logger("test_ingestion")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        reset_config()

    def test_numpy_encoder_serializes_numpy_types(self):
        """Test that NumpyEncoder handles numpy types correctly."""
        import numpy as np
        data = {
            "int64_val": np.int64(123),
            "float64_val": np.float64(45.67),
            "array_val": np.array([1, 2, 3])
        }
        
        # Should not raise TypeError
        result = json.dumps(data, cls=NumpyEncoder)
        parsed = json.loads(result)
        
        self.assertEqual(parsed["int64_val"], 123)
        self.assertEqual(parsed["float64_val"], 45.67)
        self.assertEqual(parsed["array_val"], [1, 2, 3])

    def test_save_data_creates_json_file(self):
        """Test that save_data writes a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        output_path = Path("data/raw/test_output.json")
        
        save_data(test_data, str(output_path))
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded, test_data)

    @patch('data.ingestion.requests.get')
    def test_fetch_url_content_success(self, mock_get):
        """Test successful URL content fetching."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"test": "data"}'
        mock_get.return_value = mock_response

        url = "https://example.com/data.json"
        content = fetch_url_content(url)

        self.assertEqual(content, '{"test": "data"}')
        mock_get.assert_called_once_with(url)

    @patch('data.ingestion.requests.get')
    def test_fetch_url_content_failure(self, mock_get):
        """Test failed URL content fetching."""
        # Mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = "https://example.com/notfound.json"
        with self.assertRaises(requests.HTTPError):
            fetch_url_content(url)

    def test_parse_compound_data_valid(self):
        """Test parsing valid compound data."""
        valid_data = {
            "compounds": [
                {"id": "C001", "name": "Test Compound", "concentration": 10.5},
                {"id": "C002", "name": "Another Compound", "concentration": 20.3}
            ]
        }

        result = parse_compound_data(valid_data)

        self.assertIn("compounds", result)
        self.assertEqual(len(result["compounds"]), 2)
        self.assertEqual(result["compounds"][0]["id"], "C001")

    def test_parse_compound_data_empty(self):
        """Test parsing empty compound data."""
        empty_data = {"compounds": []}
        result = parse_compound_data(empty_data)
        self.assertEqual(len(result["compounds"]), 0)

    def test_parse_compound_data_invalid(self):
        """Test parsing invalid compound data."""
        invalid_data = {"wrong_key": []}
        result = parse_compound_data(invalid_data)
        self.assertNotIn("compounds", result)

    @patch('data.ingestion.requests.get')
    def test_fetch_compound_data_with_verified_url(self, mock_get):
        """Test fetching compound data when verified URL exists."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "compounds": [
                {"id": "C001", "name": "Real Compound", "concentration": 15.0}
            ]
        })
        mock_get.return_value = mock_response

        # Update config to have a verified URL
        config = get_config()
        config.verified_urls['compound'] = "https://example.com/compounds.json"

        with patch('data.ingestion.fetch_url_content', return_value=mock_response.text):
            result = fetch_compound_data()

        self.assertIn("compounds", result)
        self.assertEqual(len(result["compounds"]), 1)

    @patch('data.ingestion.generate_mock_compound_data')
    def test_fetch_compound_data_with_mock(self, mock_gen):
        """Test fetching compound data falls back to mock when no verified URL."""
        # Ensure no verified URL
        config = get_config()
        config.verified_urls['compound'] = None

        # Mock the generator
        mock_data = {
            "compounds": [
                {"id": "M001", "name": "Mock Compound", "concentration": 5.0}
            ]
        }
        mock_gen.return_value = mock_data

        result = fetch_compound_data()

        self.assertIn("compounds", result)
        self.assertEqual(len(result["compounds"]), 1)
        mock_gen.assert_called_once()

    def test_save_data_creates_file(self):
        """Test that save_data creates the output file."""
        test_data = {"test": "value"}
        output_path = Path(self.test_dir) / "test_output.json"

        save_data(test_data, output_path)

        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

    def test_save_data_creates_directories(self):
        """Test that save_data creates parent directories if needed."""
        test_data = {"test": "value"}
        output_path = Path(self.test_dir) / "new_dir" / "nested" / "output.json"

        save_data(test_data, output_path)

        self.assertTrue(output_path.exists())

    @patch('data.ingestion.fetch_compound_data')
    @patch('data.ingestion.save_data')
    def test_run_all_ingestion_calls_functions(self, mock_save, mock_fetch):
        """Test that run_all_ingestion calls the appropriate functions."""
        mock_fetch.return_value = {"compounds": []}

        run_all_ingestion(self.test_dir)

        mock_fetch.assert_called_once()
        mock_save.assert_called_once()
        # Verify the save path is correct
        call_args = mock_save.call_args
        self.assertIn("compound_data.json", str(call_args[0][1]))

    @patch('data.ingestion.fetch_url_content')
    def test_fetch_url_content_with_timeout(self, mock_fetch):
        """Test handling of timeout errors."""
        mock_fetch.side_effect = requests.Timeout("Connection timed out")

        url = "https://slow-example.com/data.json"
        with self.assertRaises(requests.Timeout):
            fetch_url_content(url)

    def test_save_data_with_nested_structure(self):
        """Test saving data with nested JSON structure."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            },
            "list": [1, 2, 3]
        }
        output_path = Path(self.test_dir) / "nested.json"

        save_data(nested_data, output_path)

        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, nested_data)

    @patch('data.ingestion.generate_mock_genomic_data')
    def test_mock_genomic_data_generation(self, mock_gen):
        """Test that mock genomic data generation works."""
        mock_data = {
            "genomic": {
                "populations": [
                    {"id": "P001", "variants": 100}
                ]
            }
        }
        mock_gen.return_value = mock_data

        result = generate_mock_genomic_data()
        self.assertIn("genomic", result)
        self.assertEqual(len(result["genomic"]["populations"]), 1)

    @patch('data.ingestion.generate_mock_environmental_data')
    def test_mock_env_data_generation(self, mock_gen):
        """Test that mock environmental data generation works."""
        mock_data = {
            "environmental": {
                "sites": [
                    {"id": "S001", "temp": 25.5}
                ]
            }
        }
        mock_gen.return_value = mock_data

        result = generate_mock_environmental_data()
        self.assertIn("environmental", result)
        self.assertEqual(len(result["environmental"]["sites"]), 1)

    def test_save_data_overwrites_existing(self):
        """Test that save_data overwrites existing files."""
        initial_data = {"version": 1}
        output_path = Path(self.test_dir) / "overwrite.json"

        # Create initial file
        save_data(initial_data, output_path)

        # Overwrite with new data
        new_data = {"version": 2}
        save_data(new_data, output_path)

        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, new_data)

    def test_parse_compound_data_with_missing_fields(self):
        """Test parsing compound data with missing optional fields."""
        partial_data = {
            "compounds": [
                {"id": "C001"},  # Missing name and concentration
                {"id": "C002", "name": "Partial"}  # Missing concentration
            ]
        }

        result = parse_compound_data(partial_data)
        self.assertEqual(len(result["compounds"]), 2)
        self.assertIn("id", result["compounds"][0])

    @patch('data.ingestion.requests.get')
    def test_fetch_url_content_with_headers(self, mock_get):
        """Test fetching URL content with custom headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "data"
        mock_get.return_value = mock_response

        url = "https://example.com/secure.json"
        fetch_url_content(url)

        # Verify requests.get was called (headers would be passed if specified in implementation)
        mock_get.assert_called_once()

    def test_run_all_ingestion_with_invalid_path(self):
        """Test run_all_ingestion with invalid output path."""
        with self.assertRaises((OSError, PermissionError)):
            # Try to write to an invalid path
            run_all_ingestion("/invalid/path/that/does/not/exist")


if __name__ == '__main__':
    unittest.main()