"""
Unit tests for AGP loader.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.ingestion.agp_loader import (
    verify_url,
    ensure_qiita_token,
    fetch_sample_mapping,
    fetch_otu_table,
    fetch_agp_data,
    build_arg_parser
)

class TestEnsureQiitaToken:
    def test_token_exists(self):
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
            token = ensure_qiita_token()
            assert token == "test_token"

    def test_token_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="QIITA_API_TOKEN environment variable is not set"):
                ensure_qiita_token()

class TestFetchSampleMapping:
    @pytest.fixture
    def mock_response(self):
        return {
            "samples": {
                "sample_1": {"fiber_intake": 25.0, "age": 30},
                "sample_2": {"fiber_intake": 15.0, "age": 40}
            }
        }

    @patch('src.ingestion.agp_loader.requests.get')
    def test_fetch_success(self, mock_get, mock_response):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response,
            raise_for_status=lambda: None
        )
        
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
            df = fetch_sample_mapping("1031", "test_token")
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "fiber_intake" in df.columns
            assert "age" in df.columns

    @patch('src.ingestion.agp_loader.requests.get')
    def test_fetch_failure(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=500,
            raise_for_status=lambda: (_ for _ in ()).throw(Exception("Server Error"))
        )
        
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
            with pytest.raises(Exception, match="Server Error"):
                fetch_sample_mapping("1031", "test_token")

class TestFetchOtuTable:
    @pytest.fixture
    def mock_otu_response(self):
        return {
            "otutable": {
                "sample_1": {"otu_1": 100, "otu_2": 50},
                "sample_2": {"otu_1": 200, "otu_2": 75}
            }
        }

    @patch('src.ingestion.agp_loader.requests.get')
    def test_fetch_success(self, mock_get, mock_otu_response):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_otu_response,
            raise_for_status=lambda: None
        )
        
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
            df = fetch_otu_table("1031", "test_token")
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "otu_1" in df.columns
            assert "otu_2" in df.columns

    @patch('src.ingestion.agp_loader.requests.get')
    def test_fetch_failure(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=500,
            raise_for_status=lambda: (_ for _ in ()).throw(Exception("Server Error"))
        )
        
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
            with pytest.raises(Exception, match="Server Error"):
                fetch_otu_table("1031", "test_token")

class TestMain:
    @patch('src.ingestion.agp_loader.fetch_agp_data')
    @patch('src.ingestion.agp_logger.get_logger')
    def test_main_success(self, mock_logger, mock_fetch):
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        mock_fetch.return_value = (pd.DataFrame(), pd.DataFrame())
        
        with patch('sys.argv', ['agp_loader.py']):
            with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
                result = main()
                assert result == 0

    @patch('src.ingestion.agp_loader.fetch_agp_data')
    @patch('src.ingestion.agp_logger.get_logger')
    def test_main_failure(self, mock_logger, mock_fetch):
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        mock_fetch.side_effect = Exception("Download failed")
        
        with patch('sys.argv', ['agp_loader.py']):
            with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
                result = main()
                assert result == 1
