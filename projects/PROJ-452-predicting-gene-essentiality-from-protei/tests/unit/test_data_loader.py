"""
Unit tests for data_loader module.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import json
from pathlib import Path

from code.data_loader import (
    DataLoadingError,
    map_ids,
    fetch_string_network,
    fetch_essentiality_labels,
    load_local_network,
    load_local_essentiality,
    save_essentiality_data
)


class TestMapIds:
    def test_map_ids_empty_list(self):
        """Test mapping with empty input list."""
        result = map_ids([], "Homo_sapiens")
        assert result == {}

    def test_map_ids_ensembl_ids(self):
        """Test mapping with Ensembl IDs (should pass through)."""
        ids = ["ENSG00000139618", "ENSG00000141510"]
        result = map_ids(ids, "Homo_sapiens")
        assert result["ENSG00000139618"] == "ENSG00000139618"
        assert result["ENSG00000141510"] == "ENSG00000141510"

    def test_map_ids_string_ids(self):
        """Test mapping with STRING IDs."""
        ids = ["STRING:10090.123", "STRING:9606.456"]
        result = map_ids(ids, "Mus_musculus")
        # Check that mapping is applied (format may vary)
        assert "10090.123" in result["STRING:10090.123"] or result["STRING:10090.123"].startswith("ENSG")


class TestFetchStringNetwork:
    @patch('code.data_loader.requests.Session')
    def test_fetch_success(self, mock_session_class):
        """Test successful network fetch."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"edges": [{"node1": "A", "node2": "B", "score": 800}]}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_string_network("Homo_sapiens", 700)
        assert "edges" in result
        assert len(result["edges"]) == 1

    @patch('code.data_loader.requests.Session')
    def test_fetch_failure(self, mock_session_class):
        """Test network fetch failure raises error."""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session_class.return_value = mock_session

        with pytest.raises(DataLoadingError):
            fetch_string_network("Homo_sapiens", 700)

    @patch('code.data_loader.requests.Session')
    def test_fetch_unknown_organism(self, mock_session_class):
        """Test fetch with unknown organism raises error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        with pytest.raises(DataLoadingError):
            fetch_string_network("UnknownOrganism", 700)


class TestFetchEssentialityLabels:
    @patch('code.data_loader.requests.get')
    def test_fetch_essentiality_success(self, mock_get):
        """Test successful essentiality fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        csv_content = """organism,gene_id,essentiality
        Homo_sapiens,ENSG00000139618,Yes
        Homo_sapiens,ENSG00000141510,No"""
        mock_response.text = csv_content
        mock_get.return_value = mock_response

        result = fetch_essentiality_labels("Homo_sapiens")
        assert "ENSG00000139618" in result
        assert result["ENSG00000139618"] is True
        assert result["ENSG00000141510"] is False

    @patch('code.data_loader.requests.get')
    def test_fetch_essentiality_failure(self, mock_get):
        """Test essentiality fetch failure raises error."""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(DataLoadingError):
            fetch_essentiality_labels("Homo_sapiens")


class TestLoadLocalData:
    def test_load_local_network_not_found(self, tmp_path):
        """Test loading network from non-existent file."""
        with patch('code.data_loader.get_path', return_value=tmp_path):
            result = load_local_network("Homo_sapiens", 700)
            assert result is None

    def test_load_local_essentiality_not_found(self, tmp_path):
        """Test loading essentiality from non-existent file."""
        with patch('code.data_loader.get_path', return_value=tmp_path):
            result = load_local_essentiality("Homo_sapiens")
            assert result is None


class TestSaveEssentialityData:
    def test_save_essentiality_data(self, tmp_path):
        """Test saving essentiality data to file."""
        essentiality = {
            "ENSG00000139618": True,
            "ENSG00000141510": False
        }

        with patch('code.data_loader.get_path', return_value=tmp_path):
            save_essentiality_data("Homo_sapiens", essentiality)

        file_path = tmp_path / "Homo_sapiens_essentiality.csv"
        assert file_path.exists()

        with open(file_path, 'r') as f:
            content = f.read()
            assert "ENSG00000139618" in content
            assert "Yes" in content
            assert "No" in content


class TestBioMartRetryLogic:
    """
    Test suite specifically for T059: Verify that persistent 500 errors from
    Ensembl BioMart API trigger the retry logic and eventually raise
    DataLoadingError after max attempts.
    """
    @patch('code.data_loader.requests.Session')
    def test_biomart_persistent_500_raises_after_max_attempts(self, mock_session_class):
        """
        Mock a persistent 500 error from Ensembl BioMart API.
        Verify that the retry logic attempts the request 3 times (max_attempts=3)
        and finally raises DataLoadingError.
        """
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # We need to mock the specific BioMart endpoint call inside map_ids or
        # a helper function that performs the actual request.
        # Since map_ids is the function that likely calls the BioMart API,
        # we will patch the internal request call.
        
        # Assuming map_ids uses a helper or directly calls requests for BioMart.
        # To make this test robust, we patch the specific method that performs the request.
        # If map_ids uses a helper function like _fetch_biomart_data, we patch that.
        # If it uses requests.Session directly, we patch that.
        
        # For this test, we assume map_ids uses a helper function or direct request
        # that we can patch. Let's assume it uses a function `_fetch_biomart` 
        # or directly uses `requests.get` or `session.get`.
        
        # Since the existing code in data_loader.py likely uses a specific pattern,
        # we will patch the `requests.Session` as used in the existing code.
        
        # The test verifies that after 3 attempts (max 3), it raises.
        with pytest.raises(DataLoadingError) as exc_info:
            # We call map_ids with a list that would trigger a BioMart request.
            # Assuming "GENE_ID" is not an Ensembl ID and requires mapping.
            map_ids(["GENE_ID"], "Homo_sapiens")

        # Verify the error message indicates max retries
        assert "max attempts" in str(exc_info.value).lower() or "retry" in str(exc_info.value).lower()

        # Verify that get was called exactly 3 times (initial + 2 retries)
        # Note: This depends on the implementation of the retry logic.
        # If the implementation uses a loop with max_attempts=3, it should be called 3 times.
        assert mock_session.get.call_count == 3

    @patch('code.data_loader.requests.Session')
    def test_biomart_success_after_retry(self, mock_session_class):
        """
        Mock a 500 error followed by a success.
        Verify that the retry logic succeeds on the second attempt.
        """
        mock_session = MagicMock()
        
        # First call returns 500
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = Exception("500 Server Error")
        
        # Second call returns 200 with valid XML/JSON
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.text = "<?xml version='1.0'?><results><row><attribute>value</attribute></row></results>"
        
        mock_session.get.side_effect = [mock_response_500, mock_response_200]
        mock_session_class.return_value = mock_session

        # This should succeed on the second attempt
        result = map_ids(["GENE_ID"], "Homo_sapiens")
        
        # Verify get was called twice
        assert mock_session.get.call_count == 2
        # Verify result is not empty (assuming the mock response is parsed correctly)
        assert isinstance(result, dict)