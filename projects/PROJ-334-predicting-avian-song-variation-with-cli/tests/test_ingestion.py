"""
Tests for the ingestion module.
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import fetch_acoustic_metadata, save_to_csv, TARGET_SPECIES

class TestIngestion:
    """Test cases for ingestion functions."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock API response."""
        return {
            'recordings': [
                {
                    'id': '12345',
                    'sp': 'Common Blackbird',
                    'filetype': 'mp3',
                    'url': 'https://xeno-canto.org/12345',
                    'dl': 'https://xeno-canto.org/12345/download',
                    'date': '2023-05-15',
                    'cnt': 'Germany',
                    'lat': 52.52,
                    'lon': 13.405,
                    'alt': 50,
                    'dur': 15.5,
                    'q': 'A',
                    'license': 'CC BY-NC 4.0',
                    'license_url': 'https://creativecommons.org/licenses/by-nc/4.0/',
                    'upl': 'Recorder123'
                },
                {
                    'id': '12346',
                    'sp': 'Common Blackbird',
                    'filetype': 'wav',
                    'url': 'https://xeno-canto.org/12346',
                    'dl': 'https://xeno-canto.org/12346/download',
                    'date': '2023-05-16',
                    'cnt': 'France',
                    'lat': 48.8566,
                    'lon': 2.3522,
                    'alt': 35,
                    'dur': 20.0,
                    'q': 'B',
                    'license': 'CC BY 4.0',
                    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                    'upl': 'Recorder456'
                }
            ],
            'numRecordings': 2,
            'numPages': 1
        }

    def test_fetch_acoustic_metadata_structure(self, mock_response):
        """Test that fetch_acoustic_metadata returns correct structure."""
        with patch('ingestion.get_session') as mock_session:
            mock_get = MagicMock()
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_session.return_value.get = mock_get

            records = fetch_acoustic_metadata("Turdus merula", max_records=10)

            assert len(records) == 2
            assert all('recording_id' in r for r in records)
            assert all('species' in r for r in records)
            assert all('lat' in r for r in records)
            assert all('lon' in r for r in records)

    def test_fetch_acoustic_metadata_species_field(self, mock_response):
        """Test that species field is correctly populated."""
        with patch('ingestion.get_session') as mock_session:
            mock_get = MagicMock()
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_session.return_value.get = mock_get

            records = fetch_acoustic_metadata("TestSpecies", max_records=10)

            assert all(r['species'] == "TestSpecies" for r in records)

    def test_save_to_csv(self, mock_response):
        """Test that save_to_csv creates a valid CSV file."""
        with patch('ingestion.get_session') as mock_session:
            mock_get = MagicMock()
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()
            mock_session.return_value.get = mock_get

            records = fetch_acoustic_metadata("Turdus merula", max_records=10)

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "test_output.csv"
                save_to_csv(records, output_path)

                assert output_path.exists()

                with open(output_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                assert len(rows) == 2
                assert 'recording_id' in rows[0]
                assert rows[0]['species'] == 'Turdus merula'

    def test_empty_records_save(self):
        """Test that save_to_csv handles empty records gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_output.csv"
            save_to_csv([], output_path)

            # File should exist but be empty or have only header
            assert output_path.exists()

    def test_target_species_list(self):
        """Test that TARGET_SPECIES is a non-empty list."""
        assert isinstance(TARGET_SPECIES, list)
        assert len(TARGET_SPECIES) > 0
        assert all(isinstance(sp, str) for sp in TARGET_SPECIES)