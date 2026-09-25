"""
Unit tests for data_loader module.
"""
import pytest
from unittest.mock import patch, MagicMock
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
