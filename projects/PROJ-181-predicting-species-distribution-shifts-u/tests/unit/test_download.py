"""
Unit tests for the download module.
"""
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from pathlib import Path
import os

# Mock the config module to avoid file system dependencies in tests
import sys
from unittest.mock import MagicMock

mock_config = MagicMock()
mock_config.PROJECT_ROOT = Path("/tmp/test_project")
mock_config.DATA_RAW_DIR = Path("/tmp/test_project/data/raw")
mock_config.SPECIES_LIST = ["Turdus migratorius"]
mock_config.HISTORICAL_START_YEAR = 1970
mock_config.HISTORICAL_END_YEAR = 2000
mock_config.RECENT_START_YEAR = 2005
mock_config.RECENT_END_YEAR = 2020
mock_config.GBIF_BASE_URL = "https://api.gbif.org/v1/occurrence/search"
mock_config.GBIF_MAX_RESULTS_PER_REQUEST = 300
mock_config.LOGS_DIR = Path("/tmp/test_project/logs")
mock_config.THINNING_DISTANCE_KM = 10.0

sys.modules['config'] = mock_config

# Mock logging config
mock_logging_config = MagicMock()
mock_logger = MagicMock()
mock_logging_config.get_download_logger.return_value = mock_logger
sys.modules['logging_config'] = mock_logging_config

from download import fetch_gbif_occurrences

class TestDownload(unittest.TestCase):

    @patch('download.requests.get')
    def test_fetch_gbif_occurrences_pagination(self, mock_get):
        """Test that pagination works correctly."""
        # Mock response for first page
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "results": [
                {"scientificName": "Turdus migratorius", "decimalLatitude": 40.0, "decimalLongitude": -75.0, "eventDate": "1990-01-01", "basisOfRecord": "OCCURRENCE", "datasetKey": "test-dataset"},
                {"scientificName": "Turdus migratorius", "decimalLatitude": 41.0, "decimalLongitude": -76.0, "eventDate": "1990-02-01", "basisOfRecord": "OCCURRENCE", "datasetKey": "test-dataset"}
            ]
        }
        mock_response1.raise_for_status = MagicMock()

        # Mock response for second page (empty)
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"results": []}
        mock_response2.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_response1, mock_response2]

        output_path = Path("/tmp/test_output.csv")
        df = fetch_gbif_occurrences(
            species_list=["Turdus migratorius"],
            year_start=1970,
            year_end=2000,
            output_path=output_path
        )

        self.assertEqual(len(df), 2)
        self.assertIn("species", df.columns)
        self.assertIn("decimalLatitude", df.columns)
        self.assertIn("download_timestamp", df.columns)
        self.assertIn("source_identifier", df.columns)
        self.assertIn("original_dataset_name", df.columns)

        # Clean up
        if output_path.exists():
            output_path.unlink()

    @patch('download.requests.get')
    def test_fetch_gbif_occurrences_missing_coordinates(self, mock_get):
        """Test that records with missing coordinates are filtered out."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"scientificName": "Turdus migratorius", "decimalLatitude": 40.0, "decimalLongitude": -75.0, "eventDate": "1990-01-01", "basisOfRecord": "OCCURRENCE", "datasetKey": "test-dataset"},
                {"scientificName": "Turdus migratorius", "decimalLatitude": None, "decimalLongitude": -75.0, "eventDate": "1990-01-01", "basisOfRecord": "OCCURRENCE", "datasetKey": "test-dataset"},
                {"scientificName": "Turdus migratorius", "decimalLatitude": 40.0, "decimalLongitude": None, "eventDate": "1990-01-01", "basisOfRecord": "OCCURRENCE", "datasetKey": "test-dataset"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        output_path = Path("/tmp/test_output2.csv")
        df = fetch_gbif_occurrences(
            species_list=["Turdus migratorius"],
            year_start=1970,
            year_end=2000,
            output_path=output_path
        )

        self.assertEqual(len(df), 1)

        # Clean up
        if output_path.exists():
            output_path.unlink()

if __name__ == "__main__":
    unittest.main()