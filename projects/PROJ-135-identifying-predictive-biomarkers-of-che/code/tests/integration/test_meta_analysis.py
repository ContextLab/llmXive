"""
Integration tests for meta_analysis module.

Tests the full flow from DE results to gene panel generation.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

import pandas as pd
import numpy as np

from src.meta_analysis import (
    load_discovery_results,
    compute_intersection,
    compute_union_top_ranked,
    save_gene_panel,
    main
)

class TestMetaAnalysisIntegration:
    @pytest.fixture
    def full_pipeline_setup(self, tmp_path):
        """Set up a complete mock pipeline for integration testing."""
        processed_dir = tmp_path / "data" / "processed"
        results_dir = tmp_path / "results"
        meta_dir = results_dir / "meta_analysis"
        
        processed_dir.mkdir(parents=True)
        meta_dir.mkdir(parents=True)
        
        # Create mock DE results for 3 tumor types
        # All types share GENE_A and GENE_B as significant
        tumor_types = ["BRCA", "LUAD", "COAD"]
        
        for tt in tumor_types:
            df = pd.DataFrame({
                'gene': ['GENE_A', 'GENE_B', 'GENE_C', 'GENE_D'],
                'pvalue': [0.001, 0.002, 0.5, 0.6],
                'padj': [0.01, 0.02, 0.8, 0.9],
                'log2FoldChange': [2.0, 1.5, 0.3, 0.4]
            })
            (processed_dir / f"{tt}_de_results.csv").to_csv(df, index=False)
        
        return {
            "processed_dir": processed_dir,
            "results_dir": results_dir,
            "meta_dir": meta_dir,
            "tumor_types": tumor_types
        }

    def test_full_meta_analysis_flow(self, full_pipeline_setup, monkeypatch):
        """Test the complete meta-analysis flow."""
        # Mock get_project_root to use our temp directory
        def mock_get_project_root():
            return full_pipeline_setup["results_dir"].parent
        
        monkeypatch.setattr("src.meta_analysis.get_project_root", mock_get_project_root)
        
        # Run the main function
        selected_genes = main()
        
        # Verify results
        assert len(selected_genes) == 2
        assert "GENE_A" in selected_genes
        assert "GENE_B" in selected_genes
        
        # Verify file was created
        output_path = full_pipeline_setup["meta_dir"] / "gene_panel.json"
        assert output_path.exists()
        
        with open(output_path) as f:
            panel_data = json.load(f)
        
        assert panel_data["panel_size"] == 2
        assert panel_data["method"] == "intersection"
        assert panel_data["fallback_reason"] is None

    def test_meta_analysis_empty_intersection_fallback(self, tmp_path, monkeypatch):
        """Test fallback to union when intersection is empty."""
        processed_dir = tmp_path / "data" / "processed"
        results_dir = tmp_path / "results"
        meta_dir = results_dir / "meta_analysis"
        
        processed_dir.mkdir(parents=True)
        meta_dir.mkdir(parents=True)
        
        # Type 1: GENE_A significant
        df1 = pd.DataFrame({
            'gene': ['GENE_A', 'GENE_B'],
            'pvalue': [0.001, 0.5],
            'padj': [0.01, 0.8],
            'log2FoldChange': [2.0, 0.3]
        })
        (processed_dir / "TYPE1_de_results.csv").to_csv(df1, index=False)
        
        # Type 2: GENE_B significant (A not)
        df2 = pd.DataFrame({
            'gene': ['GENE_A', 'GENE_B'],
            'pvalue': [0.5, 0.001],
            'padj': [0.8, 0.01],
            'log2FoldChange': [0.3, 2.0]
        })
        (processed_dir / "TYPE2_de_results.csv").to_csv(df2, index=False)
        
        def mock_get_project_root():
            return tmp_path
        
        monkeypatch.setattr("src.meta_analysis.get_project_root", mock_get_project_root)
        
        selected_genes = main()
        
        # Should fall back to union
        assert len(selected_genes) > 0
        assert "GENE_A" in selected_genes or "GENE_B" in selected_genes
        
        output_path = meta_dir / "gene_panel.json"
        with open(output_path) as f:
            panel_data = json.load(f)
        
        assert panel_data["method"] == "union_top_ranked"
        assert panel_data["fallback_reason"] == "intersection_empty"

    def test_meta_analysis_insufficient_types(self, tmp_path, monkeypatch):
        """Test behavior with only 1 tumor type (should fail or warn)."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Only one type
        df = pd.DataFrame({
            'gene': ['GENE_A', 'GENE_B'],
            'pvalue': [0.001, 0.5],
            'padj': [0.01, 0.8],
            'log2FoldChange': [2.0, 0.3]
        })
        (processed_dir / "BRCA_de_results.csv").to_csv(df, index=False)
        
        def mock_get_project_root():
            return tmp_path
        
        monkeypatch.setattr("src.meta_analysis.get_project_root", mock_get_project_root)
        
        # Should still run but return empty intersection and use union
        selected_genes = main()
        
        # Union of top-ranked from single type
        assert len(selected_genes) > 0
        assert "GENE_A" in selected_genes