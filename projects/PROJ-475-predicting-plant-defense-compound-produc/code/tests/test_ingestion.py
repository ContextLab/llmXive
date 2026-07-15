"""
Unit tests for ingestion logic (T017).
Tests mocked downloads and data handling for genomic, environmental, and compound data.
"""
import unittest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import logging

# Adjust imports to match project structure
# Assuming tests are run from project root or code/ is in sys.path
try:
    from data.ingestion import (
        fetch_url_content,
        parse_vcf_content,
        save_data,
        fetch_genomic_data,
        fetch_env_data,
        fetch_compound_data,
        run_all_ingestion
    )
    from data.mock_generator import (
        generate_mock_genomic_data,
        generate_mock_environmental_data,
        generate_mock_compound_data
    )
    from utils.logging import configure_root_logger, get_module_logger
except ImportError as e:
    # Fallback for running directly if path setup differs
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.ingestion import (
        fetch_url_content,
        parse_vcf_content,
        save_data,
        fetch_genomic_data,
        fetch_env_data,
        fetch_compound_data,
        run_all_ingestion
    )
    from data.mock_generator import (
        generate_mock_genomic_data,
        generate_mock_environmental_data,
        generate_mock_compound_data
    )
    from utils.logging import configure_root_logger, get_module_logger

# Configure logging for tests
configure_root_logger()
logger = get_module_logger("test_ingestion")


class TestFetchUrlContent(unittest.TestCase):
    """Tests for the fetch_url_content function."""

    def test_fetch_url_content_success(self):
        """Test successful URL fetch."""
        mock_response = MagicMock()
        mock_response.content = b"Mocked content"
        mock_response.status_code = 200

        with patch('data.ingestion.requests.get', return_value=mock_response) as mock_get:
            result = fetch_url_content("http://example.com/data.json")
            mock_get.assert_called_once_with("http://example.com/data.json")
            self.assertEqual(result, b"Mocked content")

    def test_fetch_url_content_failure(self):
        """Test URL fetch failure (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        with patch('data.ingestion.requests.get', return_value=mock_response):
            with self.assertRaises(Exception):
                fetch_url_content("http://example.com/missing.json")


class TestParseVcfContent(unittest.TestCase):
    """Tests for the parse_vcf_content function."""

    def test_parse_vcf_content_valid(self):
        """Test parsing valid VCF content."""
        vcf_content = """##fileformat=VCFv4.2
        ##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
        #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
        1\t100\t.\tA\tT\t30\tPASS\tDP=10
        1\t200\t.\tG\tC\t20\tPASS\tDP=15
        """
        expected = [
            {'CHROM': '1', 'POS': '100', 'ID': '.', 'REF': 'A', 'ALT': 'T', 'QUAL': '30', 'FILTER': 'PASS', 'INFO': 'DP=10'},
            {'CHROM': '1', 'POS': '200', 'ID': '.', 'REF': 'G', 'ALT': 'C', 'QUAL': '20', 'FILTER': 'PASS', 'INFO': 'DP=15'}
        ]
        
        result = parse_vcf_content(vcf_content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], expected[0])
        self.assertEqual(result[1], expected[1])

    def test_parse_vcf_content_empty(self):
        """Test parsing empty VCF content."""
        result = parse_vcf_content("")
        self.assertEqual(result, [])


class TestSaveData(unittest.TestCase):
    """Tests for the save_data function."""

    def setUp(self):
        """Set up temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.test_dir, "test_output.json")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_save_data_creates_json_file(self):
        """Test that save_data creates a valid JSON file."""
        data = {"key": "value", "number": 123}
        save_data(data, self.output_path)
        
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, data)

    def test_save_data_overwrites_existing(self):
        """Test that save_data overwrites existing files."""
        initial_data = {"initial": "data"}
        with open(self.output_path, 'w') as f:
            json.dump(initial_data, f)
        
        new_data = {"updated": "data"}
        save_data(new_data, self.output_path)
        
        with open(self.output_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, new_data)


class TestFetchGenomicData(unittest.TestCase):
    """Tests for fetch_genomic_data with mocked downloads."""

    def test_fetch_genomic_data_from_verified_url(self):
        """Test fetching genomic data when verified URL is configured."""
        mock_response = MagicMock()
        mock_response.content = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t100\t.\tA\tT\t30\tPASS\tDP=10"
        mock_response.status_code = 200
        
        # Mock config to have a verified URL
        with patch('data.ingestion.requests.get', return_value=mock_response):
            with patch('data.ingestion.config.get_config') as mock_config:
                mock_config.return_value.verified_urls = {'genomic': 'http://example.com/genomic.vcf'}
                
                # We need to mock save_data to avoid writing to disk in this specific test context
                # or ensure the directory exists. For unit test isolation, we mock save_data.
                with patch('data.ingestion.save_data') as mock_save:
                    result = fetch_genomic_data()
                    mock_save.assert_called_once()
                    self.assertIsNotNone(result)

    def test_fetch_genomic_data_fallback_to_mock(self):
        """Test fetching genomic data falls back to mock when no verified URL."""
        with patch('data.ingestion.config.get_config') as mock_config:
            mock_config.return_value.verified_urls = {}
            
            with patch('data.ingestion.generate_mock_genomic_data') as mock_gen:
                mock_gen.return_value = {"mock": "genomic_data"}
                with patch('data.ingestion.save_data') as mock_save:
                    result = fetch_genomic_data()
                    mock_gen.assert_called_once()
                    self.assertEqual(result, {"mock": "genomic_data"})


class TestFetchEnvData(unittest.TestCase):
    """Tests for fetch_env_data with mocked downloads."""

    def test_fetch_env_data_from_verified_url(self):
        """Test fetching environmental data when verified URL is configured."""
        mock_response = MagicMock()
        mock_response.content = b'{"env": "data"}'
        mock_response.status_code = 200
        
        with patch('data.ingestion.requests.get', return_value=mock_response):
            with patch('data.ingestion.config.get_config') as mock_config:
                mock_config.return_value.verified_urls = {'env': 'http://example.com/env.json'}
                
                with patch('data.ingestion.save_data') as mock_save:
                    result = fetch_env_data()
                    mock_save.assert_called_once()
                    self.assertIsNotNone(result)

    def test_fetch_env_data_fallback_to_mock(self):
        """Test fetching environmental data falls back to mock when no verified URL."""
        with patch('data.ingestion.config.get_config') as mock_config:
            mock_config.return_value.verified_urls = {}
            
            with patch('data.ingestion.generate_mock_environmental_data') as mock_gen:
                mock_gen.return_value = {"mock": "env_data"}
                with patch('data.ingestion.save_data') as mock_save:
                    result = fetch_env_data()
                    mock_gen.assert_called_once()
                    self.assertEqual(result, {"mock": "env_data"})


class TestFetchCompoundData(unittest.TestCase):
    """Tests for fetch_compound_data with mocked downloads."""

    def test_fetch_compound_data_from_verified_url(self):
        """Test fetching compound data when verified URL is configured."""
        mock_response = MagicMock()
        mock_response.content = b'{"compound": "data"}'
        mock_response.status_code = 200
        
        with patch('data.ingestion.requests.get', return_value=mock_response):
            with patch('data.ingestion.config.get_config') as mock_config:
                mock_config.return_value.verified_urls = {'compound': 'http://example.com/compound.json'}
                
                with patch('data.ingestion.save_data') as mock_save:
                    result = fetch_compound_data()
                    mock_save.assert_called_once()
                    self.assertIsNotNone(result)

    def test_fetch_compound_data_fallback_to_mock(self):
        """Test fetching compound data falls back to mock when no verified URL."""
        with patch('data.ingestion.config.get_config') as mock_config:
            mock_config.return_value.verified_urls = {}
            
            with patch('data.ingestion.generate_mock_compound_data') as mock_gen:
                mock_gen.return_value = {"mock": "compound_data"}
                with patch('data.ingestion.save_data') as mock_save:
                    result = fetch_compound_data()
                    mock_gen.assert_called_once()
                    self.assertEqual(result, {"mock": "compound_data"})


class TestRunAllIngestion(unittest.TestCase):
    """Tests for the run_all_ingestion orchestration function."""

    def test_run_all_ingestion_calls_all_fetchers(self):
        """Test that run_all_ingestion calls all fetch functions."""
        with patch('data.ingestion.fetch_genomic_data') as mock_gen:
            with patch('data.ingestion.fetch_env_data') as mock_env:
                with patch('data.ingestion.fetch_compound_data') as mock_comp:
                    run_all_ingestion()
                    
                    mock_gen.assert_called_once()
                    mock_env.assert_called_once()
                    mock_comp.assert_called_once()


if __name__ == '__main__':
    unittest.main()