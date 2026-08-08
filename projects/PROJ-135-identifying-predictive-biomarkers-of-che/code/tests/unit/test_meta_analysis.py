"""
Unit tests for meta_analysis module.

Tests:
- compute_intersection: intersection logic across tumor types
- compute_union_top_ranked: fallback union logic
- save_gene_panel: JSON output structure
- load_discovery_results: file loading and validation
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

import pandas as pd
import numpy as np

# Import module under test
from src.meta_analysis import (
    load_discovery_results,
    compute_intersection,
    compute_union_top_ranked,
    save_gene_panel,
    FDR_THRESHOLD,
    LOG2FC_THRESHOLD
)

@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary project structure with mock DE results."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create mock DE results for 3 tumor types
    tumor_types = ["BRCA", "LUAD", "COAD"]
    
    # BRCA: genes A, B, C significant
    brca_df = pd.DataFrame({
        'gene': ['GENE_A', 'GENE_B', 'GENE_C', 'GENE_D', 'GENE_E'],
        'pvalue': [0.001, 0.002, 0.003, 0.5, 0.6],
        'padj': [0.01, 0.02, 0.03, 0.8, 0.9],
        'log2FoldChange': [2.0, 1.5, 1.2, 0.5, 0.3]
    })
    (processed_dir / "BRCA_de_results.csv").to_csv(brca_df, index=False)
    
    # LUAD: genes A, B significant (C not sig)
    luad_df = pd.DataFrame({
        'gene': ['GENE_A', 'GENE_B', 'GENE_C', 'GENE_F', 'GENE_G'],
        'pvalue': [0.001, 0.002, 0.1, 0.4, 0.5],
        'padj': [0.01, 0.02, 0.5, 0.7, 0.8],
        'log2FoldChange': [2.0, 1.5, 0.5, 0.4, 0.3]
    })
    (processed_dir / "LUAD_de_results.csv").to_csv(luad_df, index=False)
    
    # COAD: genes A, B significant
    coad_df = pd.DataFrame({
        'gene': ['GENE_A', 'GENE_B', 'GENE_H', 'GENE_I', 'GENE_J'],
        'pvalue': [0.001, 0.002, 0.3, 0.4, 0.5],
        'padj': [0.01, 0.02, 0.6, 0.7, 0.8],
        'log2FoldChange': [2.0, 1.5, 0.4, 0.3, 0.2]
    })
    (processed_dir / "COAD_de_results.csv").to_csv(coad_df, index=False)
    
    return {
        "processed_dir": processed_dir,
        "tumor_types": tumor_types
    }

@pytest.fixture
def temp_project_empty_intersection(tmp_path):
    """Create a structure where no gene is significant in all types."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Type 1: Gene X significant
    df1 = pd.DataFrame({
        'gene': ['GENE_X', 'GENE_Y', 'GENE_Z'],
        'pvalue': [0.001, 0.5, 0.6],
        'padj': [0.01, 0.8, 0.9],
        'log2FoldChange': [2.0, 0.3, 0.4]
    })
    (processed_dir / "TYPE1_de_results.csv").to_csv(df1, index=False)
    
    # Type 2: Gene Y significant (X not)
    df2 = pd.DataFrame({
        'gene': ['GENE_X', 'GENE_Y', 'GENE_W'],
        'pvalue': [0.5, 0.001, 0.6],
        'padj': [0.8, 0.01, 0.9],
        'log2FoldChange': [0.3, 2.0, 0.4]
    })
    (processed_dir / "TYPE2_de_results.csv").to_csv(df2, index=False)
    
    return {
        "processed_dir": processed_dir,
        "tumor_types": ["TYPE1", "TYPE2"]
    }

@pytest.fixture
def temp_project_top_ranked(tmp_path):
    """Create a structure for testing top-ranked union."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Type 1: A, B, C significant
    df1 = pd.DataFrame({
        'gene': ['GENE_A', 'GENE_B', 'GENE_C', 'GENE_D'],
        'pvalue': [0.001, 0.002, 0.003, 0.5],
        'padj': [0.01, 0.02, 0.03, 0.8],
        'log2FoldChange': [2.0, 1.5, 1.2, 0.3]
    })
    (processed_dir / "TYPE1_de_results.csv").to_csv(df1, index=False)
    
    # Type 2: B, C, D significant
    df2 = pd.DataFrame({
        'gene': ['GENE_A', 'GENE_B', 'GENE_C', 'GENE_D'],
        'pvalue': [0.5, 0.001, 0.002, 0.003],
        'padj': [0.8, 0.01, 0.02, 0.03],
        'log2FoldChange': [0.3, 2.0, 1.5, 1.2]
    })
    (processed_dir / "TYPE2_de_results.csv").to_csv(df2, index=False)
    
    return {
        "processed_dir": processed_dir,
        "tumor_types": ["TYPE1", "TYPE2"]
    }

class TestLoadDiscoveryResults:
    def test_load_discovery_results_success(self, temp_project_structure):
        """Test successful loading of DE results."""
        results = load_discovery_results(
            temp_project_structure["processed_dir"],
            temp_project_structure["tumor_types"]
        )
        
        assert len(results) == 3
        assert "BRCA" in results
        assert "LUAD" in results
        assert "COAD" in results
        
        # Check structure
        assert "gene" in results["BRCA"].columns
        assert "padj" in results["BRCA"].columns
        assert "log2FoldChange" in results["BRCA"].columns

    def test_load_discovery_results_missing_file(self, temp_project_structure):
        """Test error when a required file is missing."""
        with pytest.raises(FileNotFoundError):
            load_discovery_results(
                temp_project_structure["processed_dir"],
                ["BRCA", "LUAD", "NONEXISTENT"]
            )

    def test_load_discovery_results_missing_columns(self, tmp_path):
        """Test error when file has invalid columns."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create file with missing columns
        df = pd.DataFrame({
            'gene': ['A', 'B'],
            'pvalue': [0.1, 0.2]
            # Missing 'padj' and 'log2FoldChange'
        })
        (processed_dir / "BRCA_de_results.csv").to_csv(df, index=False)
        
        with pytest.raises(ValueError, match="missing columns"):
            load_discovery_results(processed_dir, ["BRCA"])

class TestComputeIntersection:
    def test_compute_intersection_non_empty(self, temp_project_structure):
        """Test intersection when genes are significant in all types."""
        results = load_discovery_results(
            temp_project_structure["processed_dir"],
            temp_project_structure["tumor_types"]
        )
        
        intersection = compute_intersection(results)
        
        # GENE_A and GENE_B are significant in all three types
        assert "GENE_A" in intersection
        assert "GENE_B" in intersection
        assert "GENE_C" not in intersection  # Not sig in LUAD
        
        assert len(intersection) == 2

    def test_compute_intersection_empty(self, temp_project_empty_intersection):
        """Test intersection when no gene is significant in all types."""
        results = load_discovery_results(
            temp_project_empty_intersection["processed_dir"],
            temp_project_empty_intersection["tumor_types"]
        )
        
        intersection = compute_intersection(results)
        
        assert len(intersection) == 0

    def test_compute_intersection_single_type(self, temp_project_structure):
        """Test that intersection requires ≥2 types."""
        results = load_discovery_results(
            temp_project_structure["processed_dir"],
            ["BRCA"]  # Only one type
        )
        
        intersection = compute_intersection(results)
        assert len(intersection) == 0

class TestComputeUnionTopRanked:
    def test_compute_union_top_ranked(self, temp_project_top_ranked):
        """Test union of top-ranked genes as fallback."""
        results = load_discovery_results(
            temp_project_top_ranked["processed_dir"],
            temp_project_top_ranked["tumor_types"]
        )
        
        # Empty intersection expected
        assert len(compute_intersection(results)) == 0
        
        # Union should include B and C (significant in both)
        union = compute_union_top_ranked(results, max_genes=50)
        
        assert "GENE_B" in union
        assert "GENE_C" in union
        # A and D appear in only one type, but may be included if max_genes allows
        assert len(union) > 0

    def test_compute_union_top_ranked_limit(self, temp_project_top_ranked):
        """Test union respects max_genes limit."""
        results = load_discovery_results(
            temp_project_top_ranked["processed_dir"],
            temp_project_top_ranked["tumor_types"]
        )
        
        union = compute_union_top_ranked(results, max_genes=2)
        assert len(union) <= 2

    def test_compute_union_top_ranked_single_type(self, temp_project_structure):
        """Test union requires ≥2 types."""
        results = load_discovery_results(
            temp_project_structure["processed_dir"],
            ["BRCA"]
        )
        
        union = compute_union_top_ranked(results)
        assert len(union) == 0

class TestSaveGenePanel:
    def test_save_gene_panel_structure(self, tmp_path):
        """Test that saved gene panel conforms to expected structure."""
        output_path = tmp_path / "gene_panel.json"
        
        selected_genes = ["GENE_A", "GENE_B", "GENE_C"]
        tumor_types = ["BRCA", "LUAD"]
        
        save_gene_panel(
            selected_genes=selected_genes,
            tumor_types=tumor_types,
            output_path=output_path,
            fallback_reason=None,
            method="intersection"
        )
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert "selected" in data
        assert data["selected"] == selected_genes
        assert data["panel_size"] == len(selected_genes)
        assert data["tumor_types_analyzed"] == tumor_types
        assert data["method"] == "intersection"
        assert data["fallback_reason"] is None
        assert "thresholds" in data
        assert data["thresholds"]["fdr"] == FDR_THRESHOLD
        assert data["thresholds"]["log2fc"] == LOG2FC_THRESHOLD

    def test_save_gene_panel_with_fallback(self, tmp_path):
        """Test saved panel includes fallback reason."""
        output_path = tmp_path / "gene_panel.json"
        
        save_gene_panel(
            selected_genes=["GENE_A"],
            tumor_types=["BRCA"],
            output_path=output_path,
            fallback_reason="intersection_empty",
            method="union_top_ranked"
        )
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert data["fallback_reason"] == "intersection_empty"
        assert data["method"] == "union_top_ranked"

    def test_save_gene_panel_creates_directory(self, tmp_path):
        """Test that save_gene_panel creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "gene_panel.json"
        
        save_gene_panel(
            selected_genes=["GENE_A"],
            tumor_types=["BRCA"],
            output_path=output_path,
            fallback_reason=None,
            method="intersection"
        )
        
        assert output_path.exists()
