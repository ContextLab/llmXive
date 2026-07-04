"""
Integration test for NASA Exoplanet Archive API download.
Verifies that the download module returns valid metadata with required fields.
"""
import os
import sys
import logging
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.download import fetch_metadata, parse_spectrum_metadata
from code.api_config import QUERY_PARAMS
from code.utils import setup_logging

# Configure logging for tests
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDownloadIntegration(unittest.TestCase):
    """
    Integration test for API download functionality.
    Validates that the download process returns metadata matching the expected schema.
    """

    @patch('code.download.requests.get')
    def test_download_returns_valid_metadata(self, mock_get):
        """
        Test that the download function returns valid metadata with required fields.
        
        Mocks the API response to simulate a successful fetch from NASA Exoplanet Archive.
        Verifies that the output DataFrame contains non-null values for:
        - equilibrium_temperature
        - host_star_metallicity
        - spectral_resolution
        - signal_to_noise_ratio
        - planet_category
        """
        # Simulate API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "pl_name": "HD 209458 b",
                    "pl_orbsper": 3.525,
                    "pl_eqt": 1359.0,
                    "st_met": 0.02,
                    "pl_resol": 100000,
                    "pl_snr": 45.5,
                    "pl_cat": "Hot Jupiter"
                },
                {
                    "pl_name": "Kepler-11 b",
                    "pl_orbsper": 10.3,
                    "pl_eqt": 900.0,
                    "st_met": -0.1,
                    "pl_resol": 50000,
                    "pl_snr": 32.1,
                    "pl_cat": "Super-Earth"
                }
            ]
        }
        mock_get.return_value = mock_response

        # Execute download
        result_df = fetch_metadata()

        # Assertions
        self.assertIsInstance(result_df, pd.DataFrame)
        self.assertGreater(len(result_df), 0, "Expected non-empty DataFrame")

        # Check required columns exist
        required_columns = [
            'planet_name',
            'equilibrium_temperature',
            'host_star_metallicity',
            'spectral_resolution',
            'signal_to_noise_ratio',
            'planet_category'
        ]
        for col in required_columns:
            self.assertIn(col, result_df.columns, f"Missing required column: {col}")

        # Check for non-null values in critical fields
        for col in ['equilibrium_temperature', 'host_star_metallicity', 
                    'spectral_resolution', 'signal_to_noise_ratio', 'planet_category']:
            self.assertFalse(result_df[col].isnull().all(), 
                             f"All values in {col} are null")

        # Verify specific values from mock data
        hd_209458 = result_df[result_df['planet_name'] == 'HD 209458 b']
        self.assertEqual(len(hd_209458), 1)
        self.assertAlmostEqual(hd_209458['equilibrium_temperature'].iloc[0], 1359.0)
        self.assertAlmostEqual(hd_209458['host_star_metallicity'].iloc[0], 0.02)
        self.assertEqual(hd_209458['planet_category'].iloc[0], 'Hot Jupiter')

    def test_parse_spectrum_metadata_extraction(self):
        """
        Test that the parsing logic correctly extracts metadata fields from raw data.
        """
        raw_data = {
            "pl_name": "WASP-12 b",
            "pl_eqt": 2500.0,
            "st_met": 0.15,
            "pl_resol": 200000,
            "pl_snr": 60.0,
            "pl_cat": "Hot Jupiter"
        }
        
        parsed = parse_spectrum_metadata(raw_data)
        
        self.assertEqual(parsed['planet_name'], 'WASP-12 b')
        self.assertEqual(parsed['equilibrium_temperature'], 2500.0)
        self.assertEqual(parsed['host_star_metallicity'], 0.15)
        self.assertEqual(parsed['spectral_resolution'], 200000)
        self.assertEqual(parsed['signal_to_noise_ratio'], 60.0)
        self.assertEqual(parsed['planet_category'], 'Hot Jupiter')

    @patch('code.download.requests.get')
    def test_download_handles_empty_response(self, mock_get):
        """
        Test that the download function handles empty API responses gracefully.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result_df = fetch_metadata()
        
        self.assertIsInstance(result_df, pd.DataFrame)
        self.assertEqual(len(result_df), 0)

    @patch('code.download.requests.get')
    def test_download_handles_api_error(self, mock_get):
        """
        Test that the download function raises appropriate error on API failure.
        """
        mock_get.side_effect = Exception("API Connection Failed")
        
        with self.assertRaises(Exception):
            fetch_metadata()

if __name__ == '__main__':
    unittest.main()