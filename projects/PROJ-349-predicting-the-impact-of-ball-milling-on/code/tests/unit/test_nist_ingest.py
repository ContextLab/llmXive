"""
Unit tests for NIST Repository Downloader (T013).

These tests verify the ingestion logic, parsing, and error handling.
They do NOT fetch real data from NIST (mocked).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd

from src.exceptions import DataIngestionError, DataFormatError
from src.ingest.nist_repo import (
    fetch_nist_data,
    parse_nist_csv,
    parse_nist_json,
    normalize_nist_schema,
    run_nist_ingestion,
    calculate_checksum
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_csv_content():
    return """experiment_id,source,material_type,milling_speed,milling_time,ball_to_powder_ratio,youngs_modulus,density,d10,d50,d90,process_duration
    NIST_001,NIST_Test,Aluminum,500,60,10,70,2.7,10,50,100,60
    NIST_002,NIST_Test,Steel,600,90,15,200,7.8,15,60,120,90
    """

@pytest.fixture
def mock_csv_path(temp_dir, mock_csv_content):
    path = temp_dir / "mock_nist.csv"
    path.write_text(mock_csv_content)
    return path

class TestHashing:
    def test_calculate_checksum(self, temp_dir):
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        checksum = calculate_checksum(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

class TestParseCSV:
    def test_parse_csv_success(self, mock_csv_content):
        df = parse_nist_csv(mock_csv_content)
        assert len(df) == 2
        assert "experiment_id" in df.columns
        assert df.iloc[0]["material_type"] == "Aluminum"

    def test_parse_csv_empty(self):
        with pytest.raises(DataIngestionError):
            parse_nist_csv("")

    def test_parse_csv_invalid_format(self):
        with pytest.raises(DataFormatError):
            parse_nist_csv("not,a,valid,csv")

class TestParseJSON:
    def test_parse_json_list(self):
        data = [
            {"experiment_id": "1", "material_type": "Cu", "d50": 50},
            {"experiment_id": "2", "material_type": "Fe", "d50": 60}
        ]
        # Mocking normalize to avoid full schema check in this unit test
        with patch('src.ingest.nist_repo.normalize_nist_schema') as mock_norm:
            mock_norm.return_value = pd.DataFrame(data)
            df = parse_nist_json(data)
            assert len(df) == 2

    def test_parse_json_dict_with_data_key(self):
        data = {"data": [{"experiment_id": "1", "material_type": "Cu"}]}
        with patch('src.ingest.nist_repo.normalize_nist_schema') as mock_norm:
            mock_norm.return_value = pd.DataFrame(data["data"])
            df = parse_nist_json(data)
            assert len(df) == 1

    def test_parse_json_no_data(self):
        with pytest.raises(DataFormatError):
            parse_nist_json({"random": "key"})

class TestNormalizeSchema:
    def test_normalize_success(self, mock_csv_content):
        df = pd.read_csv(pd.io.common.StringIO(mock_csv_content))
        result = normalize_nist_schema(df)
        assert "experiment_id" in result.columns
        assert "source" in result.columns

    def test_normalize_missing_columns(self):
        df = pd.DataFrame({"wrong_col": [1]})
        with pytest.raises(DataIngestionError):
            normalize_nist_schema(df)

class TestFetchData:
    @patch('src.ingest.nist_repo.requests.get')
    def test_fetch_csv_success(self, mock_get, mock_csv_content):
        mock_response = MagicMock()
        mock_response.text = mock_csv_content
        mock_response.headers = {'content-type': 'text/csv'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = fetch_nist_data("TEST_ID")
        assert len(df) == 2
        mock_get.assert_called_once()

    @patch('src.ingest.nist_repo.requests.get')
    def test_fetch_json_success(self, mock_get):
        mock_data = [{"experiment_id": "1", "material_type": "Cu", "d50": 50}]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch('src.ingest.nist_repo.normalize_nist_schema') as mock_norm:
            mock_norm.return_value = pd.DataFrame(mock_data)
            df = fetch_nist_data("TEST_ID")
            assert len(df) == 1

    def test_fetch_no_id(self):
        with pytest.raises(DataIngestionError):
            fetch_nist_data(None)

    @patch('src.ingest.nist_repo.requests.get')
    def test_fetch_failure(self, mock_get):
        mock_get.side_effect = Exception("Network Error")
        with pytest.raises(DataIngestionError):
            fetch_nist_data("TEST_ID")

class TestRunIngestion:
    @patch('src.ingest.nist_repo.fetch_nist_data')
    @patch('src.ingest.nist_repo.OUTPUT_DIR')
    @patch('src.ingest.nist_repo.OUTPUT_FILE')
    def test_run_ingestion_success(self, mock_output_file, mock_output_dir, mock_fetch, temp_dir, mock_csv_content):
        # Setup mocks
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.parent = temp_dir
        mock_output_file.__truediv__ = lambda self, name: temp_dir / name
        
        mock_df = pd.read_csv(pd.io.common.StringIO(mock_csv_content))
        mock_fetch.return_value = mock_df

        # Mock calculate_checksum to avoid file I/O in test
        with patch('src.ingest.nist_repo.calculate_checksum', return_value="abc123"):
            result = run_nist_ingestion("TEST_ID")
            
            # Verify output file path logic
            assert result is not None
            mock_fetch.assert_called_once_with("TEST_ID")

    @patch('src.ingest.nist_repo.fetch_nist_data')
    def test_run_ingestion_empty_data(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        with pytest.raises(DataIngestionError):
            run_nist_ingestion("TEST_ID")