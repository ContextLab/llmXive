import pytest
import os
import sys
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from itertools import islice

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetch_xeno_canto import (
    calculate_sha256,
    fetch_page,
    fetch_xeno_canto_data,
    write_to_csv,
    OUTPUT_FILE,
    CHECKSUMS_FILE,
    STATE_FILE
)

class TestCalculateSha256:
    def test_calculate_sha256_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        try:
            checksum = calculate_sha256(temp_path)
            # SHA256 of empty file
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256_with_content(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        try:
            checksum = calculate_sha256(temp_path)
            # SHA256 of "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

class TestFetchPage:
    @patch('fetch_xeno_canto.requests.get')
    def test_fetch_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "recordings": [
                {"sp": "Turdus merula", "lat": 51.5, "lon": -0.1, "id": "123", "file": "test.wav"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_page(1)
        assert len(result) == 1
        assert result[0]["sp"] == "Turdus merula"
        mock_get.assert_called_once()

    @patch('fetch_xeno_canto.requests.get')
    def test_fetch_page_empty_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"recordings": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_page(1)
        assert len(result) == 0

    @patch('fetch_xeno_canto.requests.get')
    def test_fetch_page_raises_on_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        with pytest.raises(Exception):
            fetch_page(1)

class TestFetchXenoCantoData:
    def test_fetch_xeno_canto_data_valid_coordinates(self):
        # Mock the fetch_page function to return valid data
        with patch('fetch_xeno_canto.fetch_page') as mock_fetch:
            mock_fetch.side_effect = [
                [
                    {"sp": "Turdus merula", "lat": 51.5, "lon": -0.1, "id": "1", "file": "test.wav"},
                    {"sp": "Parus major", "lat": 52.0, "lon": 0.5, "id": "2", "file": "test2.wav"}
                ],
                []  # Empty page to stop iteration
            ]
            
            records = list(fetch_xeno_canto_data())
            assert len(records) == 2
            assert records[0]["species_id"] == "Turdus merula"
            assert records[0]["lat"] == 51.5
            assert records[0]["lon"] == -0.1

    def test_fetch_xeno_canto_data_invalid_coordinates_skipped(self):
        with patch('fetch_xeno_canto.fetch_page') as mock_fetch:
            mock_fetch.side_effect = [
                [
                    {"sp": "Turdus merula", "lat": "invalid", "lon": -0.1, "id": "1", "file": "test.wav"},
                    {"sp": "Parus major", "lat": None, "lon": 0.5, "id": "2", "file": "test2.wav"},
                    {"sp": "Erithacus rubecula", "lat": 53.0, "lon": 1.0, "id": "3", "file": "test3.wav"}
                ],
                []
            ]
            
            records = list(fetch_xeno_canto_data())
            # Only the valid record should be included
            assert len(records) == 1
            assert records[0]["species_id"] == "Erithacus rubecula"

    def test_fetch_xeno_canto_data_out_of_bounds_skipped(self):
        with patch('fetch_xeno_canto.fetch_page') as mock_fetch:
            mock_fetch.side_effect = [
                [
                    {"sp": "Turdus merula", "lat": 91.0, "lon": -0.1, "id": "1", "file": "test.wav"},  # Lat out of bounds
                    {"sp": "Parus major", "lat": 52.0, "lon": 181.0, "id": "2", "file": "test2.wav"},  # Lon out of bounds
                    {"sp": "Erithacus rubecula", "lat": 53.0, "lon": 1.0, "id": "3", "file": "test3.wav"}
                ],
                []
            ]
            
            records = list(fetch_xeno_canto_data())
            assert len(records) == 1
            assert records[0]["species_id"] == "Erithacus rubecula"

class TestWriteToCsv:
    def test_write_to_csv_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            
            records = [
                {"species_id": "Turdus merula", "lat": 51.5, "lon": -0.1, "rec_id": "1", "file": "test.wav", "song_type": "song", "country": "GB"},
                {"species_id": "Parus major", "lat": 52.0, "lon": 0.5, "rec_id": "2", "file": "test2.wav", "song_type": "call", "country": "DE"}
            ]
            
            count = write_to_csv(iter(records), output_path)
            
            assert count == 2
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["species_id"] == "Turdus merula"
                assert float(rows[0]["lat"]) == 51.5

    def test_write_to_csv_empty_iterator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output_empty.csv"
            
            count = write_to_csv(iter([]), output_path)
            
            assert count == 0
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 0

class TestIntegration:
    @patch('fetch_xeno_canto.fetch_page')
    def test_full_pipeline(self, mock_fetch):
        mock_fetch.side_effect = [
            [
                {"sp": "Turdus merula", "lat": 51.5, "lon": -0.1, "id": "1", "file": "test.wav"},
                {"sp": "Parus major", "lat": 52.0, "lon": 0.5, "id": "2", "file": "test2.wav"}
            ],
            []
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override OUTPUT_FILE for test
            test_output = Path(tmpdir) / "xeno_canto_metadata.csv"
            
            records = fetch_xeno_canto_data()
            count = write_to_csv(records, test_output)
            
            assert count == 2
            assert test_output.exists()
            
            # Verify checksum can be calculated
            from fetch_xeno_canto import calculate_sha256
            checksum = calculate_sha256(test_output)
            assert len(checksum) == 64  # SHA256 hex length