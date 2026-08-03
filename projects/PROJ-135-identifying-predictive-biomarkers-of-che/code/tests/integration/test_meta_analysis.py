"""
Integration test for meta-analysis pipeline.
Tests the full flow from discovery results to gene panel generation.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.meta_analysis import (
    compute_intersection,
    compute_union_top_ranked,
    save_gene_panel
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestMetaAnalysisIntegration:
    """Integration tests for meta-analysis functionality."""

    @pytest.fixture
    def full_project_structure(self):
        """Create a complete project structure with mock data for integration test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create full directory structure
            data_processed = tmpdir_path / "data" / "processed"
            results_meta = tmpdir_path / "results" / "meta_analysis"
            data_processed.mkdir(parents=True, exist_ok=True)
            results_meta.mkdir(parents=True, exist_ok=True)
            
            # Create mock discovery results for 4 tumor types
            # Scenario: 3 types have overlap, 1 doesn't
            gene_data = {
                "BRCA": {
                    "significant_genes": [
                        {"gene": "TP53", "pvalue": 1e-15, "log2fc": 3.2},
                        {"gene": "BRCA1", "pvalue": 1e-12, "log2fc": 2.8},
                        {"gene": "EGFR", "pvalue": 1e-10, "log2fc": 2.1},
                        {"gene": "KRAS", "pvalue": 1e-8, "log2fc": 1.5}
                    ]
                },
                "LUAD": {
                    "significant_genes": [
                        {"gene": "TP53", "pvalue": 1e-14, "log2fc": 3.0},
                        {"gene": "BRCA1", "pvalue": 1e-11, "log2fc": 2.5},
                        {"gene": "EGFR", "pvalue": 1e-9, "log2fc": 2.0},
                        {"gene": "ALK", "pvalue": 1e-7, "log2fc": 1.8}
                    ]
                },
                "COAD": {
                    "significant_genes": [
                        {"gene": "TP53", "pvalue": 1e-13, "log2fc": 2.9},
                        {"gene": "BRCA1", "pvalue": 1e-10, "log2fc": 2.4},
                        {"gene": "EGFR", "pvalue": 1e-8, "log2fc": 1.9},
                        {"gene": "APC", "pvalue": 1e-6, "log2fc": 1.6}
                    ]
                },
                "PRAD": {
                    "significant_genes": [
                        {"gene": "TP53", "pvalue": 1e-12, "log2fc": 2.7},
                        {"gene": "BRCA1", "pvalue": 1e-9, "log2fc": 2.2},
                        {"gene": "ERG", "pvalue": 1e-7, "log2fc": 1.7},
                        {"gene": "TMPRSS2", "pvalue": 1e-5, "log2fc": 1.4}
                    ]
                }
            }
            
            for tt, data in gene_data.items():
                results_file = data_processed / f"{tt}_discovery_de_results.json"
                with open(results_file, 'w') as f:
                    json.dump(data, f)
            
            yield tmpdir_path, data_processed, results_meta

    def test_full_intersection_pipeline(self, full_project_structure):
        """Test complete intersection pipeline with 4 tumor types."""
        tmpdir_path, _, results_meta = full_project_structure
        
        tumor_types = ["BRCA", "LUAD", "COAD", "PRAD"]
        
        # Compute intersection
        intersection_genes = compute_intersection(tumor_types, tmpdir_path)
        
        # Expected: TP53 and BRCA1 are in all 4 types
        assert len(intersection_genes) == 2
        assert "TP53" in intersection_genes
        assert "BRCA1" in intersection_genes
        
        # Save the panel
        output_path = results_meta / "gene_panel.json"
        save_gene_panel(intersection_genes, output_path, intersection_used=True)
        
        # Verify saved file
        assert output_path.exists()
        with open(output_path, 'r') as f:
            panel_data = json.load(f)
        
        assert panel_data["panel_size"] == 2
        assert panel_data["method"] == "intersection"
        assert set(panel_data["genes"]) == {"TP53", "BRCA1"}

    def test_fallback_to_union_when_empty(self, full_project_structure):
        """Test fallback to union when intersection is empty."""
        tmpdir_path, data_processed, results_meta = full_project_structure
        
        # Remove overlap by creating a scenario with no common genes
        # Create a new tumor type with unique genes
        unique_data = {
            "significant_genes": [
                {"gene": "UNIQUE_A", "pvalue": 1e-10, "log2fc": 2.5},
                {"gene": "UNIQUE_B", "pvalue": 1e-8, "log2fc": 2.0}
            ]
        }
        
        unique_file = data_processed / "UNIQUE_discovery_de_results.json"
        with open(unique_file, 'w') as f:
            json.dump(unique_data, f)
        
        # Now try intersection with the unique type
        tumor_types = ["BRCA", "UNIQUE"]
        intersection_genes = compute_intersection(tumor_types, tmpdir_path)
        
        # Should be empty
        assert len(intersection_genes) == 0
        
        # Fallback to union
        union_genes = compute_union_top_ranked(tumor_types, tmpdir_path, max_genes=3)
        
        # Should have genes from both
        assert len(union_genes) > 0
        assert "UNIQUE_A" in union_genes or "UNIQUE_B" in union_genes
        
        # Save with fallback flag
        output_path = results_meta / "gene_panel_fallback.json"
        save_gene_panel(union_genes, output_path, intersection_used=False,
                       fallback_reason="intersection_empty")
        
        # Verify
        with open(output_path, 'r') as f:
            panel_data = json.load(f)
        
        assert panel_data["method"] == "union_fallback"
        assert panel_data["fallback_reason"] == "intersection_empty"

    def test_pipeline_with_mixed_ranking(self, full_project_structure):
        """Test pipeline with genes that have different ranking orders."""
        tmpdir_path, _, results_meta = full_project_structure
        
        tumor_types = ["BRCA", "LUAD", "COAD"]
        
        # Compute intersection
        intersection_genes = compute_intersection(tumor_types, tmpdir_path)
        
        # Should have TP53, BRCA1, EGFR
        assert len(intersection_genes) == 3
        assert "TP53" in intersection_genes
        assert "BRCA1" in intersection_genes
        assert "EGFR" in intersection_genes
        
        # Save and verify
        output_path = results_meta / "gene_panel_mixed.json"
        save_gene_panel(intersection_genes, output_path, intersection_used=True)
        
        with open(output_path, 'r') as f:
            panel_data = json.load(f)
        
        assert panel_data["panel_size"] == 3
        assert set(panel_data["genes"]) == {"TP53", "BRCA1", "EGFR"}

    def test_pipeline_handles_large_gene_sets(self, full_project_structure):
        """Test pipeline with larger gene sets to ensure performance."""
        tmpdir_path, data_processed, results_meta = full_project_structure
        
        # Create a tumor type with many significant genes
        large_data = {
            "significant_genes": [
                {"gene": f"GENE_{i:03d}", "pvalue": 10**(-i), "log2fc": 2.0 - i*0.01}
                for i in range(100)
            ]
        }
        
        large_file = data_processed / "LARGE_discovery_de_results.json"
        with open(large_file, 'w') as f:
            json.dump(large_data, f)
        
        # Add one common gene
        large_data["significant_genes"].append(
            {"gene": "COMMON_GENE", "pvalue": 1e-10, "log2fc": 3.0}
        )
        
        with open(large_file, 'w') as f:
            json.dump(large_data, f)
        
        # Test intersection with the large set
        tumor_types = ["BRCA", "LARGE"]
        intersection_genes = compute_intersection(tumor_types, tmpdir_path)
        
        # Should find the common gene
        assert "COMMON_GENE" in intersection_genes
        
        # Test union with max_genes limit
        union_genes = compute_union_top_ranked(tumor_types, tmpdir_path, max_genes=10)
        
        # Should be limited to 10 from each
        assert len(union_genes) <= 20
        assert "COMMON_GENE" in union_genes