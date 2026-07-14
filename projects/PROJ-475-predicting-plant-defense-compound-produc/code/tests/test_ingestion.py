import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    fetch_genomic_vcf_from_verified_url,
    fetch_environmental_metadata_from_verified_url,
    fetch_compound_profiles_from_verified_url,
    ingest_genomic_data,
    ingest_environmental_data,
    ingest_compound_data,
    main
)
from config import get_config
from utils.logging import get_module_logger

logger = get_module_logger(__name__)

class TestIngestion(unittest.TestCase):
    """Unit tests for ingestion logic (T017)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create necessary directory structure
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        
        # Create a minimal config for testing
        self.config_path = os.path.join(self.test_dir, "config.yaml")
        with open(self.config_path, "w") as f:
            f.write("""
        paths:
          raw_data: data/raw
          processed_data: data/processed
        verified_urls:
          genomic: null
          env: null
          compound: null
        seeds:
          data: 42
        """)
        
        # Patch get_config to return our test config
        self.config = get_config(self.config_path)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('data.ingestion.requests.get')
    def test_fetch_genomic_vcf_from_verified_url_success(self, mock_get):
        """Test successful genomic VCF fetch from verified URL."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "mock_vcf_content"}'
        mock_get.return_value = mock_response

        config = self.config
        config.verified_urls['genomic'] = 'https://example.com/genomic.vcf'
        
        result = fetch_genomic_vcf_from_verified_url(config)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        mock_get.assert_called_once()

    @patch('data.ingestion.requests.get')
    def test_fetch_genomic_vcf_from_verified_url_failure(self, mock_get):
        """Test genomic VCF fetch handles network failure."""
        mock_get.side_effect = Exception("Network error")
        
        config = self.config
        config.verified_urls['genomic'] = 'https://example.com/genomic.vcf'
        
        # Should fall back to mock data generator when URL fails
        result = fetch_genomic_vcf_from_verified_url(config)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))

    @patch('data.ingestion.requests.get')
    def test_fetch_environmental_metadata_success(self, mock_get):
        """Test successful environmental metadata fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"stations": [{"id": 1, "lat": 0, "lon": 0}]}
        mock_get.return_value = mock_response

        config = self.config
        config.verified_urls['env'] = 'https://example.com/env.json'
        
        result = fetch_environmental_metadata_from_verified_url(config)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))

    @patch('data.ingestion.requests.get')
    def test_fetch_compound_profiles_success(self, mock_get):
        """Test successful compound profiles fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"compounds": [{"id": 1, "name": "test"}]}
        mock_get.return_value = mock_response

        config = self.config
        config.verified_urls['compound'] = 'https://example.com/compounds.json'
        
        result = fetch_compound_profiles_from_verified_url(config)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))

    def test_ingest_genomic_data_uses_mock_when_no_url(self):
        """Test that genomic ingestion falls back to mock when no verified URL."""
        config = self.config
        config.verified_urls['genomic'] = None
        
        result_path = ingest_genomic_data(config)
        
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))
        
        # Verify file content is valid JSON
        with open(result_path, 'r') as f:
            data = json.load(f)
            self.assertIn('data', data)

    def test_ingest_environmental_data_uses_mock_when_no_url(self):
        """Test that environmental ingestion falls back to mock when no verified URL."""
        config = self.config
        config.verified_urls['env'] = None
        
        result_path = ingest_environmental_data(config)
        
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))

    def test_ingest_compound_data_uses_mock_when_no_url(self):
        """Test that compound ingestion falls back to mock when no verified URL."""
        config = self.config
        config.verified_urls['compound'] = None
        
        result_path = ingest_compound_data(config)
        
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))

    @patch('data.ingestion.ingest_genomic_data')
    @patch('data.ingestion.ingest_environmental_data')
    @patch('data.ingestion.ingest_compound_data')
    @patch('data.ingestion.main')
    def test_main_pipeline_calls_all_ingestors(self, mock_main, mock_compound, mock_env, mock_genomic):
        """Test that main pipeline orchestrates all ingestion steps."""
        # Setup mocks
        mock_genomic.return_value = "path/to/genomic.json"
        mock_env.return_value = "path/to/env.json"
        mock_compound.return_value = "path/to/compound.json"
        
        # Run main
        with patch('sys.argv', ['main']):
            main()
        
        # Verify all ingestion functions were called
        mock_genomic.assert_called_once()
        mock_env.assert_called_once()
        mock_compound.assert_called_once()

    def test_ingestion_creates_output_files(self):
        """Test that ingestion creates the expected output files."""
        config = self.config
        config.verified_urls['genomic'] = None
        config.verified_urls['env'] = None
        config.verified_urls['compound'] = None
        
        # Run ingestion
        ingest_genomic_data(config)
        ingest_environmental_data(config)
        ingest_compound_data(config)
        
        # Check files exist
        self.assertTrue(os.path.exists(os.path.join(config.paths.raw_data, "genomic_vcf.json")))
        self.assertTrue(os.path.exists(os.path.join(config.paths.raw_data, "env_data.json")))
        self.assertTrue(os.path.exists(os.path.join(config.paths.raw_data, "compound_data.json")))

if __name__ == '__main__':
    unittest.main()