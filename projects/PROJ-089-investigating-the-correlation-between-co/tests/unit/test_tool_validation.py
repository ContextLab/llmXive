import os
import csv
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

# Import the function to test
from utils import validate_tools_and_log

class TestToolValidation:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Create a temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, "tool_validation_log.csv")
        self.citations_path = os.path.join(self.temp_dir, "citations.csv")
        
        # Yield for test execution
        yield self.log_path, self.citations_path, self.temp_dir
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('utils.requests.get')
    def test_pass_by_stars(self, mock_get, log_path, citations_path, temp_dir):
        """Test that a repo with > 5000 stars passes."""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"stargazers_count": 6000}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Run validation
        result = validate_tools_and_log("test_owner", "test_repo", log_path=log_path, citations_path=citations_path)

        # Assert results
        assert result["status"] == "PASS"
        assert result["stars"] == 6000
        assert result["citation_found"] is False
        assert result["repo_id"] == "test_owner/test_repo"

        # Verify log file content
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['status'] == 'PASS'

    @patch('utils.requests.get')
    def test_pass_by_citation(self, mock_get, log_path, citations_path, temp_dir):
        """Test that a repo with < 5000 stars passes if citation exists."""
        # Mock GitHub API response (low stars)
        mock_response = MagicMock()
        mock_response.json.return_value = {"stargazers_count": 100}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Create mock citations.csv
        with open(citations_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["paper_title", "author"])
            writer.writerow(["Study on test_repo", "John Doe"])

        # Run validation
        result = validate_tools_and_log("test_owner", "test_repo", log_path=log_path, citations_path=citations_path)

        # Assert results
        assert result["status"] == "PASS"
        assert result["stars"] == 100
        assert result["citation_found"] is True

    @patch('utils.requests.get')
    def test_fail_no_stars_no_citation(self, mock_get, log_path, citations_path, temp_dir):
        """Test that a repo fails if stars <= 5000 and no citation."""
        # Mock GitHub API response (low stars)
        mock_response = MagicMock()
        mock_response.json.return_value = {"stargazers_count": 100}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Ensure citations file does not exist or has no match
        # (citations_path is empty/non-existent by default in fixture)

        # Run validation
        result = validate_tools_and_log("test_owner", "test_repo", log_path=log_path, citations_path=citations_path)

        # Assert results
        assert result["status"] == "FAIL"
        assert result["stars"] == 100
        assert result["citation_found"] is False

    @patch('utils.requests.get')
    def test_api_failure_falls_to_citation(self, mock_get, log_path, citations_path, temp_dir):
        """Test behavior when API call fails but citation exists."""
        # Mock API failure
        mock_get.side_effect = requests.RequestException("Network error")

        # Create mock citations.csv
        with open(citations_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["paper_title", "author"])
            writer.writerow(["Study on test_repo", "John Doe"])

        # Run validation
        result = validate_tools_and_log("test_owner", "test_repo", log_path=log_path, citations_path=citations_path)

        # Assert results
        assert result["status"] == "PASS"
        assert result["stars"] == 0
        assert result["citation_found"] is True