"""
Unit tests for data ingestion logic.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    fetch_genomic_data,
    fetch_environmental_data,
    fetch_compound_data,
    run_all_ingestion,
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
import logging

class TestIngestion(unittest.TestCase):
    """Test cases for ingestion module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = load_config()
        
        # Override paths for testing
        self.config.paths.raw = Path(self.temp_dir)
        self.config.paths.processed = Path(self.temp_dir) / "processed"
        
        # Mock the global config
        import config
        config._global_config = self.config

        configure_root_logger = logging.getLogger()
        configure_root_logger.setLevel(logging.WARNING)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_data_with_numpy_types(self):
        """Test that save_data handles numpy types correctly."""
        data = {
            "value": 10,
            "score": 3.14,
            "list": [1, 2, 3]
        }
        output_path = Path(self.temp_dir) / "test.json"
        
        save_data(data, str(output_path))
        
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded["value"], 10)
        self.assertAlmostEqual(loaded["score"], 3.14, places=2)

    def test_fetch_genomic_data_fallback(self):
        """Test that genomic fetch falls back to mock data when URL fails."""
        # Ensure no verified URL is set or it fails
        self.config.verified_urls['genomic'] = 'http://invalid-url-that-will-fail.example.com'
        
        data = fetch_genomic_data()
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # Check structure
        first_record = data[0]
        self.assertIn('population_id', first_record)
        self.assertIn('genotypes', first_record)

    def test_fetch_environmental_data_fallback(self):
        """Test that environmental fetch falls back to mock data when URL fails."""
        self.config.verified_urls['env'] = 'http://invalid-url-that-will-fail.example.com'
        
        data = fetch_environmental_data()
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        first_record = data[0]
        self.assertIn('env_id', first_record)
        self.assertIn('population_id', first_record)

    def test_fetch_compound_data_fallback(self):
        """Test that compound fetch falls back to mock data when URL fails."""
        self.config.verified_urls['compound'] = 'http://invalid-url-that-will-fail.example.com'
        
        data = fetch_compound_data()
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        first_record = data[0]
        self.assertIn('compound_id', first_record)
        self.assertIn('population_id', first_record)

    def test_run_all_ingestion(self):
        """Test the full ingestion pipeline."""
        self.config.verified_urls['genomic'] = 'http://invalid.example.com'
        self.config.verified_urls['env'] = 'http://invalid.example.com'
        self.config.verified_urls['compound'] = 'http://invalid.example.com'
        
        results = run_all_ingestion()
        
        self.assertIn('genomic', results)
        self.assertIn('env', results)
        self.assertIn('compound', results)
        
        self.assertIsInstance(results['genomic'], list)
        self.assertIsInstance(results['env'], list)
        self.assertIsInstance(results['compound'], list)

    def test_numpy_encoder(self):
        """Test NumpyEncoder handles various numpy types."""
        import numpy as np
        
        data = {
            "int64": np.int64(42),
            "float64": np.float64(3.14),
            "array": np.array([1, 2, 3])
        }
        
        encoder = NumpyEncoder()
        serialized = encoder.default(data["int64"])
        self.assertEqual(serialized, 42)
        
        serialized = encoder.default(data["float64"])
        self.assertAlmostEqual(serialized, 3.14)
        
        serialized = encoder.default(data["array"])
        self.assertEqual(serialized, [1, 2, 3])

if __name__ == '__main__':
    unittest.main()