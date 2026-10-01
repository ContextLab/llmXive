"""
Unit tests for refactored utils module.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from code.utils.oa_checker import is_open_access, check_doi_oa_status
from code.utils.logging_config import setup_logging, test_log_entry
from code.utils.parsers import extract_sample_size, extract_effect_size
from code.utils.api_client import OpenMLClient, fetch_top_classification_datasets

class TestOAChecker:
    def test_is_open_access_success(self):
        """Test OA check with a successful response."""
        with patch('code.utils.oa_checker.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.headers = {"Content-Type": "application/pdf"}
            mock_head.return_value = mock_response
            
            assert is_open_access("http://example.com/doc.pdf") is True

    def test_is_open_access_fail(self):
        """Test OA check with a failed response."""
        with patch('code.utils.oa_checker.requests.head') as mock_head:
            mock_head.side_effect = Exception("Connection error")
            
            assert is_open_access("http://example.com/doc.pdf") is False

    def test_check_doi_oa_status_success(self):
        """Test DOI OA check with successful response."""
        mock_data = {
            "message": {
                "license": [{"URL": "https://creativecommons.org/licenses/by/4.0/"}]
            }
        }
        with patch('code.utils.oa_checker.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = check_doi_oa_status("10.1000/xyz")
            assert result["is_open"] is True
            assert result["license"] == "https://creativecommons.org/licenses/by/4.0/"

class TestLoggingConfig:
    def test_setup_logging(self, tmp_path):
        """Test logging setup writes to file."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(str(log_file), level=logging.INFO)
        logger.info("Test message")
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content

    def test_test_log_entry(self, tmp_path):
        """Test test_log_entry function."""
        log_file = tmp_path / "test.log"
        setup_logging(str(log_file), level=logging.INFO)
        result = test_log_entry()
        
        assert result is True
        assert log_file.exists()

class TestParsers:
    def test_extract_sample_size(self):
        """Test sample size extraction."""
        text = "The study included N=150 participants."
        assert extract_sample_size(text) == 150

    def test_extract_cohens_d(self):
        """Test Cohen's d extraction."""
        text = "We found a large effect size (Cohen's d = 0.85)."
        value, metric, df = extract_effect_size(text)
        assert metric == "Cohen's d"
        assert value == 0.85
        assert df is None

    def test_extract_f_statistic(self):
        """Test F-statistic extraction."""
        text = "The result was significant, F(2, 50) = 4.56."
        value, metric, df = extract_effect_size(text)
        assert metric == "F"
        assert value == 4.56
        assert df == (2, 50)

class TestAPIClient:
    def test_openml_client_init(self):
        """Test OpenMLClient initialization."""
        client = OpenMLClient()
        assert client.base_url == "https://www.openml.org/api/v1"
        assert client.session is not None

    @patch('code.utils.api_client.requests.Session.get')
    def test_fetch_top_datasets(self, mock_get):
        """Test fetching datasets."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "datasets": {
                "dataset": [
                    {"dataset_id": 1, "name": "Test"},
                    {"dataset_id": 2, "name": "Test2"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        datasets = fetch_top_classification_datasets(limit=2)
        assert len(datasets) == 2
        assert datasets[0]["dataset_id"] == 1