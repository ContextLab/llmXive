"""
Unit tests for the data ingestion logic (T017).
Tests mocked downloads and fallback to mock data generation.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    fetch_genomic_data,
    fetch_environmental_data,
    fetch_compound_data,
    run_genomic_ingestion,
    run_env_ingestion,
    run_compound_ingestion,
    save_data,
    NumpyEncoder
)
from data.mock_generator import (
    generate_mock_genomic_data,
    generate_mock_environmental_data,
    generate_mock_compound_data
)
from config import load_config, get_config
from utils.logging import configure_root_logger

configure_root_logger()

class TestIngestion(unittest.TestCase):
    """Unit tests for ingestion logic with mocked downloads."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create necessary subdirectories
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        # Create a minimal config file for testing
        config_content = {
            "paths": {
                "raw_data": "data/raw",
                "processed_data": "data/processed",
                "output_dir": "data/results"
            },
            "verified_urls": {
                "genomic": None,  # Force mock fallback for tests
                "env": None,
                "compound": None
            },
            "seeds": {
                "genomic": 42,
                "env": 43,
                "compound": 44
            }
        }
        
        with open("config.yaml", "w") as f:
            json.dump(config_content, f)
        
        # Reload config to pick up test config
        self.config = get_config()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

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
    def test_fetch_genomic_data_uses_mock_when_no_url(self, mock_get):
        """Test genomic fetch falls back to mock when no verified URL."""
        # Mock config to have no verified URL
        with patch('data.ingestion.get_config') as mock_cfg:
            mock_cfg.return_value = self.config
            mock_cfg.return_value.verified_urls = {"genomic": None}
            
            result = fetch_genomic_data()
            
            # Should not call requests.get
            mock_get.assert_not_called()
            
            # Should return valid data structure
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)
            self.assertIn("population_id", result[0])

    @patch('data.ingestion.requests.get')
    def test_fetch_genomic_data_fetches_from_url_when_available(self, mock_get):
        """Test genomic fetch uses real URL when available."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"population_id": "P1", "variants": 100}]
        mock_get.return_value = mock_response
        
        test_config = self.config
        test_config.verified_urls = {"genomic": "https://example.com/genomic.json"}
        
        with patch('data.ingestion.get_config', return_value=test_config):
            result = fetch_genomic_data()
            
            mock_get.assert_called_once()
            self.assertEqual(result, [{"population_id": "P1", "variants": 100}])

    @patch('data.ingestion.requests.get')
    def test_fetch_environmental_data_uses_mock_when_no_url(self, mock_get):
        """Test environmental fetch falls back to mock when no verified URL."""
        with patch('data.ingestion.get_config') as mock_cfg:
            mock_cfg.return_value = self.config
            mock_cfg.return_value.verified_urls = {"env": None}
            
            result = fetch_environmental_data()
            
            mock_get.assert_not_called()
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)
            self.assertIn("env_id", result[0])

    @patch('data.ingestion.requests.get')
    def test_fetch_compound_data_uses_mock_when_no_url(self, mock_get):
        """Test compound fetch falls back to mock when no verified URL."""
        with patch('data.ingestion.get_config') as mock_cfg:
            mock_cfg.return_value = self.config
            mock_cfg.return_value.verified_urls = {"compound": None}
            
            result = fetch_compound_data()
            
            mock_get.assert_not_called()
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)
            self.assertIn("compound_id", result[0])

    def test_run_genomic_ingestion_writes_output(self):
        """Test that run_genomic_ingestion writes the expected output file."""
        with patch('data.ingestion.get_config') as mock_cfg:
            mock_cfg.return_value = self.config
            mock_cfg.return_value.verified_urls = {"genomic": None}
            
            output_file = run_genomic_ingestion()
            
            expected_path = Path("data/raw/genomic_vcf.json")
            self.assertTrue(expected_path.exists())
            self.assertEqual(output_file, str(expected_path))
            
            with open(expected_path, 'r') as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)

    def test_run_env_ingestion_writes_output(self):
        """Test that run_env_ingestion writes the expected output file."""
        with patch('data.ingestion.get_config') as mock_cfg:
            mock_cfg.return_value = self.config
            mock_cfg.return_value.verified_urls = {"env": None}
            
            output_file = run_env_ingestion()
            
            expected_path = Path("data/raw/env_data.json")
            self.assertTrue(expected_path.exists())
            self.assertEqual(output_file, str(expected_path))
            
            with open(expected_path, 'r') as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)

    def test_run_compound_ingestion_writes_output(self):
        """Test that run_compound_ingestion writes the expected output file."""
        with patch('data.ingestion.get_config') as mock_cfg:
            mock_cfg.return_value = self.config
            mock_cfg.return_value.verified_urls = {"compound": None}
            
            output_file = run_compound_ingestion()
            
            expected_path = Path("data/raw/compound_data.json")
            self.assertTrue(expected_path.exists())
            self.assertEqual(output_file, str(expected_path))
            
            with open(expected_path, 'r') as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)

    def test_deterministic_mock_generation(self):
        """Test that mock generation is deterministic with fixed seed."""
        # Generate twice with same seed
        data1 = generate_mock_genomic_data(seed=42, n_populations=5)
        data2 = generate_mock_genomic_data(seed=42, n_populations=5)
        
        self.assertEqual(data1, data2)
        
        # Different seed should produce different data
        data3 = generate_mock_genomic_data(seed=43, n_populations=5)
        self.assertNotEqual(data1, data3)

    def test_mock_data_has_required_fields(self):
        """Test that generated mock data has all required fields."""
        genomic = generate_mock_genomic_data(n_populations=10)
        env_data = generate_mock_environmental_data(n_populations=10)
        compounds = generate_mock_compound_data(n_populations=10)
        
        # Check genomic fields
        self.assertIn("population_id", genomic[0])
        self.assertIn("variants", genomic[0])
        
        # Check env fields
        self.assertIn("env_id", env_data[0])
        self.assertIn("temperature", env_data[0])
        
        # Check compound fields
        self.assertIn("compound_id", compounds[0])
        self.assertIn("concentration", compounds[0])

if __name__ == '__main__':
    unittest.main()