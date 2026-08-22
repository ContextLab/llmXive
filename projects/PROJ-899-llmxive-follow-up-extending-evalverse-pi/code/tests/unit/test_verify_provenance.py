"""
Unit tests for provenance verification functionality.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.verify_provenance import (
    check_url_reachable,
    extract_doi_from_url,
    verify_provenance,
    save_provenance_result
)


class TestUrlReachability:
    """Tests for URL reachability checking."""

    @patch('urllib.request.urlopen')
    def test_url_reachable_success(self, mock_urlopen):
        """Test successful URL reachability check."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = check_url_reachable("https://example.com")
        assert result is True

    @patch('urllib.request.urlopen')
    def test_url_reachable_redirect(self, mock_urlopen):
        """Test URL reachability with redirect (302)."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 302
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = check_url_reachable("https://example.com")
        assert result is True

    @patch('urllib.request.urlopen')
    def test_url_reachable_failure(self, mock_urlopen):
        """Test failed URL reachability check."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection failed")
        
        result = check_url_reachable("https://example.com")
        assert result is False


class TestDoiExtraction:
    """Tests for DOI extraction from URLs."""

    def test_extract_doi_from_doi_org_url(self):
        """Test DOI extraction from doi.org URL."""
        url = "https://doi.org/10.5281/zenodo.12345"
        doi = extract_doi_from_url(url)
        assert doi == "10.5281/zenodo.12345"

    def test_extract_doi_from_zenodo_url(self):
        """Test DOI extraction from Zenodo URL."""
        url = "https://zenodo.org/record/12345"
        doi = extract_doi_from_url(url)
        assert doi == "10.5281/zenodo.12345"

    def test_extract_doi_no_match(self):
        """Test DOI extraction when no pattern matches."""
        url = "https://example.com/some/random/path"
        doi = extract_doi_from_url(url)
        assert doi is None


class TestVerifyProvenance:
    """Tests for the main provenance verification function."""

    @patch('src.data.verify_provenance.check_url_reachable')
    @patch('src.data.verify_provenance.extract_doi_from_url')
    @patch('src.data.verify_provenance.get_raw_data_dir')
    def test_verify_provenance_success(
        self, mock_data_dir, mock_extract_doi, mock_check_url
    ):
        """Test successful provenance verification."""
        # Setup mocks
        mock_check_url.return_value = True
        mock_extract_doi.return_value = "10.5281/zenodo.12345"
        
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = [MagicMock()]  # Non-empty
        mock_data_dir.return_value = mock_dir
        
        # Patch DATASET_DOI
        with patch('src.data.verify_provenance.DATASET_DOI', "10.5281/zenodo.12345"):
            result = verify_provenance()
            
            assert result["status"] == "pass"
            assert result["url_reachable"] is True
            assert result["doi_match"] is True
            assert result["data_exists"] is True

    @patch('src.data.verify_provenance.check_url_reachable')
    @patch('src.data.verify_provenance.extract_doi_from_url')
    @patch('src.data.verify_provenance.get_raw_data_dir')
    def test_verify_provenance_url_failure(
        self, mock_data_dir, mock_extract_doi, mock_check_url
    ):
        """Test provenance verification when URL is not reachable."""
        # Setup mocks
        mock_check_url.return_value = False
        mock_extract_doi.return_value = None
        
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = [MagicMock()]
        mock_data_dir.return_value = mock_dir
        
        result = verify_provenance()
        
        assert result["status"] == "fail"
        assert result["url_reachable"] is False
        assert "URL" in result["errors"][0]

    @patch('src.data.verify_provenance.check_url_reachable')
    @patch('src.data.verify_provenance.extract_doi_from_url')
    @patch('src.data.verify_provenance.get_raw_data_dir')
    def test_verify_provenance_doi_mismatch(
        self, mock_data_dir, mock_extract_doi, mock_check_url
    ):
        """Test provenance verification when DOI does not match."""
        # Setup mocks
        mock_check_url.return_value = True
        mock_extract_doi.return_value = "10.5281/zenodo.99999"
        
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = [MagicMock()]
        mock_data_dir.return_value = mock_dir
        
        with patch('src.data.verify_provenance.DATASET_DOI', "10.5281/zenodo.12345"):
            result = verify_provenance()
            
            assert result["status"] == "fail"
            assert result["doi_match"] is False
            assert "DOI mismatch" in result["errors"][0]

    @patch('src.data.verify_provenance.check_url_reachable')
    @patch('src.data.verify_provenance.extract_doi_from_url')
    @patch('src.data.verify_provenance.get_raw_data_dir')
    def test_verify_provenance_data_missing(
        self, mock_data_dir, mock_extract_doi, mock_check_url
    ):
        """Test provenance verification when local data is missing."""
        # Setup mocks
        mock_check_url.return_value = True
        mock_extract_doi.return_value = "10.5281/zenodo.12345"
        
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = []  # Empty
        mock_data_dir.return_value = mock_dir
        
        with patch('src.data.verify_provenance.DATASET_DOI', "10.5281/zenodo.12345"):
            result = verify_provenance()
            
            assert result["status"] == "fail"
            assert result["data_exists"] is False
            assert "Local data" in result["errors"][0]


class TestSaveProvenanceResult:
    """Tests for saving provenance results."""

    def test_save_provenance_result_creates_file(self, tmp_path):
        """Test that save_provenance_result creates the output file."""
        result = {
            "status": "pass",
            "url_reachable": True,
            "doi_match": True,
            "data_exists": True,
            "errors": [],
            "warnings": []
        }
        
        output_path = tmp_path / "test_provenance.json"
        saved_path = save_provenance_result(result, output_path)
        
        assert saved_path == output_path
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["status"] == "pass"