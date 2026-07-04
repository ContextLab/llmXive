"""
Unit tests for download.py functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from download import (
    parse_spectrum_metadata, 
    validate_parsed_metadata, 
    process_download_metadata,
    fetch_spectrum_data
)
from config import get_config


class TestDownload(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_raw_data = [
            {
                'pl_name': 'HD 209458 b',
                'pl_eqt': '1450',
                'st_met': '0.02',
                'spec_res': '1000',
                'hst_snr': '15.2',
                'jwst_snr': '22.1',
                'pl_type': 'Hot Jupiter'
            },
            {
                'pl_name': 'Kepler-10 b',
                'pl_eqt': '2400',
                'st_met': '-0.15',
                'spec_res': '500',
                'hst_snr': '3.2',
                'jwst_snr': '4.1',
                'pl_type': 'Super Earth'
            }
        ]
        
    def test_parse_spectrum_metadata(self):
        """Test parsing of raw metadata into structured format."""
        parsed = parse_spectrum_metadata(self.sample_raw_data)
        
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['planet_name'], 'HD 209458 b')
        self.assertEqual(parsed[0]['equilibrium_temp_k'], 1450.0)
        self.assertEqual(parsed[0]['host_star_metallicity'], 0.02)
        self.assertEqual(parsed[0]['spectral_resolution_r'], 1000.0)
        self.assertEqual(parsed[0]['snr_hst'], 15.2)
        self.assertEqual(parsed[0]['snr_jwst'], 22.1)
        self.assertEqual(parsed[0]['category'], 'Hot Jupiter')
        self.assertFalse(parsed[0]['censored'])
        
        # Check censored data detection
        self.assertTrue(parsed[1]['censored'])
        self.assertEqual(parsed[1]['category'], 'Censored')
        
    def test_validate_parsed_metadata(self):
        """Test validation of parsed metadata."""
        # Valid data
        valid_data = [
            {
                'planet_name': 'Test',
                'equilibrium_temp_k': 1000.0,
                'host_star_metallicity': 0.1,
                'spectral_resolution_r': 500.0,
                'snr_hst': 10.0,
                'snr_jwst': 15.0,
                'category': 'Hot Jupiter'
            }
        ]
        self.assertTrue(validate_parsed_metadata(valid_data))
        
        # Invalid data (missing field)
        invalid_data = [
            {
                'planet_name': 'Test',
                'equilibrium_temp_k': 1000.0,
                # Missing other required fields
            }
        ]
        self.assertFalse(validate_parsed_metadata(invalid_data))
        
    def test_process_download_metadata(self):
        """Test saving metadata to CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_metadata.csv"
            metadata = [
                {
                    'planet_name': 'Test',
                    'equilibrium_temp_k': 1000.0,
                    'host_star_metallicity': 0.1,
                    'spectral_resolution_r': 500.0,
                    'snr_hst': 10.0,
                    'snr_jwst': 15.0,
                    'category': 'Hot Jupiter'
                }
            ]
            
            process_download_metadata(metadata, output_path)
            
            self.assertTrue(output_path.exists())
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('planet_name', content)
                self.assertIn('Test', content)
                
    @patch('download.fetch_spectrum_data')
    def test_fetch_spectrum_data(self, mock_fetch):
        """Test fetch_spectrum_data function."""
        mock_fetch.return_value = (Path('/tmp/raw'), [])
        raw_dir, metadata = fetch_spectrum_data()
        
        self.assertIsInstance(raw_dir, Path)
        self.assertIsInstance(metadata, list)
