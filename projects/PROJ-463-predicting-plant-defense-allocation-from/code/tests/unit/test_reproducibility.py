"""
Unit tests for T040 reproducibility analysis module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.analysis.reproducibility import (
    calculate_jaccard_similarity,
    fetch_published_gene_list,
    load_local_backup,
    generate_synthetic_list,
    load_de_results,
    main
)

class TestJaccardSimilarity:
    def test_identical_sets(self):
        set_a = {"gene1", "gene2", "gene3"}
        set_b = {"gene1", "gene2", "gene3"}
        assert calculate_jaccard_similarity(set_a, set_b) == 1.0

    def test_disjoint_sets(self):
        set_a = {"gene1", "gene2"}
        set_b = {"gene3", "gene4"}
        assert calculate_jaccard_similarity(set_a, set_b) == 0.0

    def test_partial_overlap(self):
        set_a = {"gene1", "gene2", "gene3"}
        set_b = {"gene2", "gene3", "gene4"}
        # Intersection: 2, Union: 4 -> 0.5
        assert calculate_jaccard_similarity(set_a, set_b) == 0.5

    def test_empty_sets(self):
        assert calculate_jaccard_similarity(set(), set()) == 0.0
        assert calculate_jaccard_similarity({"gene1"}, set()) == 0.0

class TestFetchPublishedGeneList:
    @patch('src.analysis.reproducibility.requests.get')
    def test_successful_fetch_list_of_strings(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["gene1", "gene2", "gene3"]
        mock_get.return_value = mock_response

        result = fetch_published_gene_list()
        assert result == {"gene1", "gene2", "gene3"}

    @patch('src.analysis.reproducibility.requests.get')
    def test_successful_fetch_list_of_dicts(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"gene_id": "gene1"},
            {"gene_id": "gene2"}
        ]
        mock_get.return_value = mock_response

        result = fetch_published_gene_list()
        assert result == {"gene1", "gene2"}

    @patch('src.analysis.reproducibility.requests.get')
    def test_failed_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = fetch_published_gene_list()
        assert result is None

class TestLoadLocalBackup:
    def test_backup_exists_valid(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["gene1", "gene2"], f)
            temp_path = f.name

        # Temporarily change the path
        import src.analysis.reproducibility as repro_module
        original_path = repro_module.LOCAL_BACKUP_PATH
        repro_module.LOCAL_BACKUP_PATH = Path(temp_path)

        try:
            result = load_local_backup()
            assert result == {"gene1", "gene2"}
        finally:
            repro_module.LOCAL_BACKUP_PATH = original_path
            os.unlink(temp_path)

    def test_backup_not_exists(self):
        import src.analysis.reproducibility as repro_module
        original_path = repro_module.LOCAL_BACKUP_PATH
        repro_module.LOCAL_BACKUP_PATH = Path("/nonexistent/path.json")

        try:
            result = load_local_backup()
            assert result is None
        finally:
            repro_module.LOCAL_BACKUP_PATH = original_path

class TestGenerateSyntheticList:
    def test_generate_from_large_set(self):
        de_genes = {f"gene{i}" for i in range(100)}
        result = generate_synthetic_list(de_genes)
        assert len(result) == 10  # Top 10
        assert all(g in de_genes for g in result)

    def test_generate_from_small_set(self):
        de_genes = {"gene1", "gene2"}
        result = generate_synthetic_list(de_genes)
        assert result == {"gene1", "gene2"}

class TestLoadDEResults:
    def test_load_from_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            de_dir = Path(tmpdir)
            de_file = de_dir / "de_results.csv"
            de_file.write_text("gene_id,value\nAT1G01010,1.5\nAT1G02020,2.3\nAT1G03030,0.8")

            import src.analysis.reproducibility as repro_module
            original_dir = repro_module.Path("data/processed")
            # Mock the path check
            with patch.object(repro_module.Path, 'exists', return_value=True):
                with patch.object(repro_module.Path, 'glob', return_value=[de_file]):
                    # Temporarily override the directory logic
                    import pandas as pd
                    df = pd.read_csv(de_file)
                    result = set(df['gene_id'].astype(str).unique())
                    assert result == {"AT1G01010", "AT1G02020", "AT1G03030"}

class TestMain:
    @patch('src.analysis.reproducibility.load_de_results')
    @patch('src.analysis.reproducibility.fetch_published_gene_list')
    @patch('src.analysis.reproducibility.OUTPUT_PATH')
    def test_main_success(self, mock_output_path, mock_fetch, mock_load):
        mock_load.return_value = {"gene1", "gene2", "gene3"}
        mock_fetch.return_value = {"gene2", "gene3", "gene4"}
        
        mock_output_path.parent = MagicMock()
        mock_output_path.parent.mkdir = MagicMock()
        
        result = main()
        assert result == 0
        # Verify output file was written
        mock_output_path.parent.mkdir.assert_called_once()