import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
from src.preprocess import map_isg_genes, process_isg_mapping_for_species, save_ortholog_mapping

class TestMapISGGenes:
    @patch('src.preprocess.requests.get')
    def test_maps_genes_successfully(self, mock_get):
        """Test successful mapping of genes to orthologs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"gene_id": "ENSMUSG00000000001"}]
        }
        mock_get.return_value = mock_response
        
        result = map_isg_genes("mus_musculus", ["ISG15"])
        assert result == ["ENSMUSG00000000001"]
        mock_get.assert_called_once()

    @patch('src.preprocess.requests.get')
    def test_handles_missing_orthologs(self, mock_get):
        """Test handling of genes with no orthologs."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = map_isg_genes("mus_musculus", ["ISG15"])
        assert result == []

    @patch('src.preprocess.requests.get')
    def test_handles_network_errors(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")
        
        result = map_isg_genes("mus_musculus", ["ISG15"])
        assert result == []

    def test_empty_gene_list(self):
        """Test with empty gene list."""
        result = map_isg_genes("mus_musculus", [])
        assert result == []

    def test_human_species(self):
        """Test with human species (should return input)."""
        result = map_isg_genes("human", ["ISG15", "MX1"])
        assert result == ["ISG15", "MX1"]

class TestProcessISGMapping:
    @patch('src.preprocess.requests.get')
    def test_process_mapping_creates_csv(self, mock_get, tmp_path):
        """Test that process_isg_mapping_for_species creates a CSV file."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"gene_id": "ENSMUSG00000000001"}]
        }
        mock_get.return_value = mock_response
        
        output_path = tmp_path / "ortholog_map.csv"
        result = process_isg_mapping_for_species("mus_musculus", ["ISG15"], output_path)
        
        assert output_path.exists()
        assert result == ["ENSMUSG00000000001"]
        
        df = pd.read_csv(output_path)
        assert "human_gene" in df.columns
        assert "ortholog_ensembl_id" in df.columns
        assert len(df) == 1

class TestSaveOrthologMapping:
    def test_save_mapping_creates_file(self, tmp_path):
        """Test that save_ortholog_mapping creates a CSV file."""
        mapping = {
            "ISG15": ["ENSMUSG00000000001"],
            "MX1": ["ENSMUSG00000000002"]
        }
        output_path = tmp_path / "ortholog_map.csv"
        
        save_ortholog_mapping(mapping, output_path)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "human_gene" in df.columns
        assert "ortholog_ensembl_id" in df.columns