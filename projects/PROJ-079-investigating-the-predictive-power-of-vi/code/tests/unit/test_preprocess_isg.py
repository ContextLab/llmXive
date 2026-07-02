import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.preprocess import map_isg_genes, process_isg_mapping_for_species, save_ortholog_mapping
from src.config import DATA_PROCESSED_PATH

class TestMapISGGenes:
    """Tests for the ISG gene mapping functionality"""

    def test_empty_gene_list(self):
        """Test that empty gene list returns empty list"""
        result = map_isg_genes("mus_musculus", [])
        assert result == []

    def test_empty_species(self):
        """Test that empty species returns empty list"""
        result = map_isg_genes("", ["ISG15"])
        assert result == []

    @patch('src.preprocess.requests.get')
    def test_successful_mapping(self, mock_get):
        """Test successful mapping of genes to orthologs"""
        # Mock response for a successful gene mapping
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "homologies": [
                    {
                        "target": {
                            "id": "ENSMUSG00000012345"
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = map_isg_genes("mus_musculus", ["ISG15"])
        assert len(result) == 1
        assert result[0] == "ENSMUSG00000012345"

    @patch('src.preprocess.requests.get')
    def test_partial_mapping(self, mock_get):
        """Test partial mapping when some genes fail"""
        # Mock successful response
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "data": {
                "homologies": [{"target": {"id": "ENSMUSG00000012345"}}]
            }
        }

        # Mock 404 response
        mock_response_not_found = MagicMock()
        mock_response_not_found.status_code = 404

        # Set up mock to return different responses based on gene
        def side_effect(url, *args, **kwargs):
            if "ISG15" in url:
                return mock_response_success
            else:
                return mock_response_not_found

        mock_get.side_effect = side_effect

        result = map_isg_genes("mus_musculus", ["ISG15", "MX1"])
        assert len(result) == 1
        assert result[0] == "ENSMUSG00000012345"

    @patch('src.preprocess.requests.get')
    def test_no_orthologs_found(self, mock_get):
        """Test when no orthologs are found for any gene"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "homologies": []  # No orthologs
            }
        }
        mock_get.return_value = mock_response

        result = map_isg_genes("mus_musculus", ["ISG15", "MX1"])
        assert result == []

    @patch('src.preprocess.requests.get')
    def test_api_error_handling(self, mock_get):
        """Test handling of API errors"""
        mock_get.side_effect = Exception("Network error")

        result = map_isg_genes("mus_musculus", ["ISG15"])
        assert result == []

    @patch('src.preprocess.requests.get')
    def test_timeout_handling(self, mock_get):
        """Test handling of request timeout"""
        mock_get.side_effect = Exception("Timeout")

        result = map_isg_genes("mus_musculus", ["ISG15"])
        assert result == []

class TestProcessISGMapping:
    """Tests for the high-level ISG mapping processing"""

    def test_empty_input(self):
        """Test with empty input lists"""
        result = process_isg_mapping_for_species("mus_musculus", [])
        assert result == []

    @patch('src.preprocess.map_isg_genes')
    @patch('src.preprocess.save_ortholog_mapping')
    def test_successful_processing(self, mock_save, mock_map):
        """Test successful processing"""
        mock_map.return_value = ["ENSMUSG00000012345", "ENSMUSG00000067890"]
        mock_save.return_value = None

        result = process_isg_mapping_for_species("mus_musculus", ["ISG15", "MX1"])
        assert len(result) == 2
        mock_map.assert_called_once_with("mus_musculus", ["ISG15", "MX1"])
        mock_save.assert_called_once()

    @patch('src.preprocess.map_isg_genes')
    @patch('src.preprocess.save_ortholog_mapping')
    def test_no_orthologs_returned(self, mock_save, mock_map):
        """Test when no orthologs are returned"""
        mock_map.return_value = []
        mock_save.return_value = None

        result = process_isg_mapping_for_species("mus_musculus", ["ISG15", "MX1"])
        assert result == []

class TestSaveOrthologMapping:
    """Tests for saving ortholog mapping to CSV"""

    def test_save_mapping_creates_file(self, tmp_path):
        """Test that save_ortholog_mapping creates a CSV file"""
        output_path = tmp_path / "test_ortholog_map.csv"
        human_genes = ["ISG15", "MX1"]
        ortholog_ids = ["ENSMUSG00000012345", "ENSMUSG00000067890"]

        save_ortholog_mapping("mus_musculus", human_genes, ortholog_ids, output_path)

        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "species" in df.columns
        assert "human_gene" in df.columns
        assert "ortholog_id" in df.columns
        assert "status" in df.columns
        assert all(df["status"] == "mapped")

    def test_save_mapping_with_failures(self, tmp_path):
        """Test saving mapping with some failures"""
        output_path = tmp_path / "test_ortholog_map.csv"
        human_genes = ["ISG15", "MX1", "OAS1"]
        ortholog_ids = ["ENSMUSG00000012345"]  # Only one mapped

        save_ortholog_mapping("mus_musculus", human_genes, ortholog_ids, output_path)

        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert df.iloc[0]["status"] == "mapped"
        assert df.iloc[1]["status"] == "failed"
        assert df.iloc[2]["status"] == "failed"
