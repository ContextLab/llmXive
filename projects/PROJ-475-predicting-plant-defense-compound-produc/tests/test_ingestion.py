"""
Unit tests for the ingestion module.

Tests mocking of downloads and verification of output.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    fetch_url_content, 
    fetch_environmental_data, 
    fetch_genomic_data, 
    fetch_compound_data,
    save_data
)
from config import reset_config, get_config

class TestIngestion(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Reset config to ensure clean state
        reset_config()
        
        # Create necessary directories
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        reset_config()

    @patch('data.ingestion.requests.get')
    def test_fetch_url_content_success(self, mock_get):
        """Test successful URL fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = fetch_url_content("http://example.com")
        
        self.assertEqual(result, {"key": "value"})
        mock_get.assert_called_once_with("http://example.com", timeout=30)

    @patch('data.ingestion.requests.get')
    def test_fetch_url_content_failure(self, mock_get):
        """Test failed URL fetch."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_url_content("http://example.com")
        
        self.assertIsNone(result)

    @patch('data.ingestion.fetch_url_content')
    @patch('data.ingestion.generate_mock_environmental_data')
    def test_fetch_environmental_data_with_verified_url(self, mock_mock_gen, mock_fetch):
        """Test environmental data fetch with verified URL."""
        mock_fetch.return_value = {"env": "data"}
        mock_mock_gen.return_value = {"env": "mock"}
        
        # Set up config with verified URL
        config = get_config()
        config.verified_urls['env'] = "http://example.com/env"
        
        result = fetch_environmental_data()
        
        self.assertEqual(result, {"env": "data"})
        mock_fetch.assert_called_once()
        mock_mock_gen.assert_not_called()

    @patch('data.ingestion.fetch_url_content')
    @patch('data.ingestion.generate_mock_environmental_data')
    def test_fetch_environmental_data_fallback_to_mock(self, mock_mock_gen, mock_fetch):
        """Test environmental data fetch falls back to mock when URL fails."""
        mock_fetch.return_value = None
        mock_mock_gen.return_value = {"env": "mock_data"}
        
        # Set up config without verified URL
        config = get_config()
        config.verified_urls['env'] = None
        
        result = fetch_environmental_data()
        
        self.assertEqual(result, {"env": "mock_data"})
        mock_mock_gen.assert_called_once()

    @patch('data.ingestion.fetch_url_content')
    @patch('data.ingestion.generate_mock_genomic_data')
    def test_fetch_genomic_data(self, mock_mock_gen, mock_fetch):
        """Test genomic data fetch logic."""
        mock_fetch.return_value = {"genomic": "real"}
        mock_mock_gen.return_value = {"genomic": "mock"}
        
        config = get_config()
        config.verified_urls['genomic'] = "http://example.com/genomic"
        
        result = fetch_genomic_data()
        
        self.assertEqual(result, {"genomic": "real"})

    @patch('data.ingestion.fetch_url_content')
    @patch('data.ingestion.generate_mock_compound_data')
    def test_fetch_compound_data(self, mock_mock_gen, mock_fetch):
        """Test compound data fetch logic."""
        mock_fetch.return_value = {"compound": "real"}
        mock_mock_gen.return_value = {"compound": "mock"}
        
        config = get_config()
        config.verified_urls['compound'] = "http://example.com/compound"
        
        result = fetch_compound_data()
        
        self.assertEqual(result, {"compound": "real"})

    def test_save_data(self):
        """Test saving data to file."""
        test_data = {"test": "value", "number": 42}
        output_path = Path("data/raw/test_output.json")
        
        save_data(test_data, output_path)
        
        self.assertTrue(output_path.exists())
        
        with open(output_path) as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data)

if __name__ == '__main__':
    unittest.main()