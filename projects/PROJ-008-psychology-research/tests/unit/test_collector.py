"""
Unit tests for the API Collector.
"""
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.data.collector import APICollector
from code.utils.config import get_data_path


class TestAPICollector:
    """Tests for APICollector class."""

    @pytest.fixture
    def collector(self, tmp_path):
        """Create a collector with a temporary data path."""
        # Temporarily override the data path
        original_get_data_path = get_data_path
        
        def mock_get_data_path():
            return tmp_path
        
        # Patch the config function
        with patch('code.data.collector.get_data_path', mock_get_data_path):
            collector = APICollector()
            yield collector

    def test_ensure_dirs(self, collector, tmp_path):
        """Test that data/raw directory is created."""
        raw_dir = tmp_path / "raw"
        assert raw_dir.exists()

    def test_load_mock_data_success(self, collector, tmp_path):
        """Test loading mock data when file exists."""
        mock_data = {
            "studies": [
                {
                    "id": "TEST001",
                    "title": "Test Study",
                    "registry": "ClinicalTrials.gov"
                }
            ]
        }
        
        mock_file = tmp_path / "raw" / "mock_registry_response.json"
        with open(mock_file, "w") as f:
            json.dump(mock_data, f)
        
        loaded_data = collector._load_mock_data()
        assert loaded_data["studies"][0]["id"] == "TEST001"

    def test_load_mock_data_missing(self, collector, tmp_path):
        """Test that FileNotFoundError is raised when mock data is missing."""
        with pytest.raises(FileNotFoundError):
            collector._load_mock_data()

    def test_log_retrieval(self, collector, tmp_path):
        """Test that retrieval events are logged correctly."""
        collector._log_retrieval("test query", 200, "test_source")
        
        log = collector.get_retrieval_log()
        assert len(log) == 1
        assert log[0]["query"] == "test query"
        assert log[0]["status_code"] == 200
        assert log[0]["source"] == "test_source"
        
        # Verify log file was written
        log_file = tmp_path / "raw" / "retrieval_log.json"
        assert log_file.exists()
        
        with open(log_file, "r") as f:
            saved_log = json.load(f)
        assert len(saved_log) == 1

    @patch('code.data.collector.os.getenv')
    def test_collect_with_mock_data(self, mock_getenv, collector, tmp_path):
        """Test collection using mock data."""
        mock_getenv.return_value = "true"
        
        mock_data = {
            "studies": [
                {"id": "NCT001", "title": "Study 1"},
                {"id": "NCT002", "title": "Study 2"}
            ]
        }
        
        mock_file = tmp_path / "raw" / "mock_registry_response.json"
        with open(mock_file, "w") as f:
            json.dump(mock_data, f)
        
        studies = collector.collect(2015, 2024)
        
        assert len(studies) == 2
        assert studies[0]["id"] == "NCT001"
        
        # Verify log contains mock entry
        log = collector.get_retrieval_log()
        assert any(e["source"] == "mock_registry_response.json" for e in log)

    @patch('code.data.collector.os.getenv')
    def test_collect_missing_mock_in_ci(self, mock_getenv, collector, tmp_path):
        """Test that collection fails when mock data is missing in CI mode."""
        mock_getenv.return_value = "true"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            collector.collect(2015, 2024)
        
        assert "Mock data missing in CI mode" in str(exc_info.value)

    def test_collect_without_mock_in_live_mode(self, collector, tmp_path):
        """Test collection without mock data in live mode."""
        # Simulate live mode (CI not set)
        with patch('code.data.collector.os.getenv', return_value=None):
            # This should attempt live API (which will fail in test without network)
            # We test that it doesn't raise FileNotFoundError for missing mock
            try:
                with patch.object(collector, '_fetch_from_api') as mock_fetch:
                    mock_fetch.return_value = {"studies": [{"id": "REAL001"}]}
                    studies = collector.collect(2015, 2024)
                    assert len(studies) == 1
            except FileNotFoundError:
                pytest.fail("Should not raise FileNotFoundError in live mode without mock")
