"""
Unit tests for the download module.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import fetch_gbif_occurrences, get_download_logger
from code.config import DATA_RAW_DIR

class TestFetchGbifOccurrences:
    """Tests for fetch_gbif_occurrences function."""

    def test_fetch_gbif_occurrences_creates_csv(self, tmp_path):
        """Test that fetch_gbif_occurrences creates a valid CSV file."""
        # Mock the requests.get to return a valid response
        mock_response_data = {
            "results": [
                {
                    "scientificName": "Turdus migratorius",
                    "decimalLatitude": 40.7128,
                    "decimalLongitude": -74.0060,
                    "eventDate": "2015-05-01",
                    "basisOfRecord": "OCCURRENCE",
                    "datasetKey": "test-dataset-key"
                },
                {
                    "scientificName": "Turdus migratorius",
                    "decimalLatitude": 41.8781,
                    "decimalLongitude": -87.6298,
                    "eventDate": "2016-06-15",
                    "basisOfRecord": "OCCURRENCE",
                    "datasetKey": "test-dataset-key"
                }
            ],
            "offset": 0,
            "limit": 300,
            "endOfRecords": True
        }

        output_path = tmp_path / "test_occurrence.csv"

        with patch('code.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            fetch_gbif_occurrences(
                species_list=["Turdus migratorius"],
                start_year=2010,
                end_year=2020,
                output_path=str(output_path),
                api_key="test-key"
            )

            # Verify the file was created
            assert output_path.exists()

            # Verify the content
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 2
                assert rows[0]['species'] == 'Turdus migratorius'
                assert rows[0]['decimalLatitude'] == '40.7128'
                assert 'source_identifier' in reader.fieldnames
                assert 'download_timestamp' in reader.fieldnames
                assert 'original_dataset_name' in reader.fieldnames

    def test_fetch_gbif_occurrences_pagination(self, tmp_path):
        """Test that pagination works correctly."""
        # First page
        page1_data = {
            "results": [{"scientificName": "Species A", "decimalLatitude": 10, "decimalLongitude": 10, "eventDate": "2010", "basisOfRecord": "OCC", "datasetKey": "K1"} for _ in range(300)],
            "offset": 0,
            "limit": 300,
            "endOfRecords": False
        }
        # Second page
        page2_data = {
            "results": [{"scientificName": "Species A", "decimalLatitude": 11, "decimalLongitude": 11, "eventDate": "2010", "basisOfRecord": "OCC", "datasetKey": "K1"} for _ in range(100)],
            "offset": 300,
            "limit": 300,
            "endOfRecords": True
        }

        output_path = tmp_path / "test_paginated.csv"

        call_count = 0
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            if call_count == 0:
                mock_response.json.return_value = page1_data
            else:
                mock_response.json.return_value = page2_data
            call_count += 1
            return mock_response

        with patch('code.download.requests.get', side_effect=mock_get_side_effect):
            fetch_gbif_occurrences(
                species_list=["Species A"],
                start_year=2010,
                end_year=2020,
                output_path=str(output_path),
                api_key="test-key"
            )

            assert call_count == 2
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Header + 300 + 100
                assert len(rows) == 401

    def test_fetch_gbif_occurrences_missing_coordinates(self, tmp_path):
        """Test that records with missing coordinates are skipped."""
        mock_response_data = {
            "results": [
                {
                    "scientificName": "Species A",
                    "decimalLatitude": 10.0,
                    "decimalLongitude": 10.0,
                    "eventDate": "2010",
                    "basisOfRecord": "OCC",
                    "datasetKey": "K1"
                },
                {
                    "scientificName": "Species A",
                    "decimalLatitude": None,
                    "decimalLongitude": None,
                    "eventDate": "2010",
                    "basisOfRecord": "OCC",
                    "datasetKey": "K1"
                }
            ],
            "offset": 0,
            "limit": 300,
            "endOfRecords": True
        }

        output_path = tmp_path / "test_missing_coords.csv"

        with patch('code.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            fetch_gbif_occurrences(
                species_list=["Species A"],
                start_year=2010,
                end_year=2020,
                output_path=str(output_path),
                api_key="test-key"
            )

            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Only the first record should be present
                assert len(rows) == 1

    def test_fetch_gbif_occurrences_no_records_raises(self, tmp_path):
        """Test that an error is raised if no records are fetched."""
        mock_response_data = {
            "results": [],
            "offset": 0,
            "limit": 300,
            "endOfRecords": True
        }

        output_path = tmp_path / "test_empty.csv"

        with patch('code.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="No records fetched from GBIF API"):
                fetch_gbif_occurrences(
                    species_list=["Species A"],
                    start_year=2010,
                    end_year=2020,
                    output_path=str(output_path),
                    api_key="test-key"
                )

def test_get_download_logger():
    """Test that get_download_logger returns a logger."""
    logger = get_download_logger()
    assert logger is not None
    assert logger.name == "download"