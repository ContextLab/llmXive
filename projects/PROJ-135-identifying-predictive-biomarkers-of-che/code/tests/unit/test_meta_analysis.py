import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add parent to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.meta_analysis import (
    load_discovery_results,
    compute_intersection,
    compute_union_top_ranked,
    update_summary_with_fallback,
    save_gene_panel,
    aggregate_and_select_panel
)

@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure with mock LOO DE results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        processed_dir = root / "data" / "processed"
        results_dir = root / "results"
        meta_dir = results_dir / "meta_analysis"
        
        processed_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)
        meta_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock LOO DE results for 3 tumor types
        # Type A: Genes 1, 2, 3 significant
        # Type B: Genes 2, 3, 4 significant
        # Type C: Genes 3, 4, 5 significant
        # Intersection: {3}
        
        data_a = {
            'gene': ['GENE1', 'GENE2', 'GENE3', 'GENE_X'],
            'pvalue': [0.01, 0.02, 0.03, 0.5],
            'log2FC': [2.0, 1.5, 1.2, 0.5],
            'significant': [True, True, True, False]
        }
        df_a = pd.DataFrame(data_a)
        df_a.to_csv(processed_dir / "loo_iteration_TypeA_de_results.csv", index=False)
        
        data_b = {
            'gene': ['GENE2', 'GENE3', 'GENE4', 'GENE_Y'],
            'pvalue': [0.01, 0.02, 0.03, 0.5],
            'log2FC': [1.5, 1.2, 2.0, 0.5],
            'significant': [True, True, True, False]
        }
        df_b = pd.DataFrame(data_b)
        df_b.to_csv(processed_dir / "loo_iteration_TypeB_de_results.csv", index=False)
        
        data_c = {
            'gene': ['GENE3', 'GENE4', 'GENE5', 'GENE_Z'],
            'pvalue': [0.01, 0.02, 0.03, 0.5],
            'log2FC': [1.2, 2.0, 1.5, 0.5],
            'significant': [True, True, True, False]
        }
        df_c = pd.DataFrame(data_c)
        df_c.to_csv(processed_dir / "loo_iteration_TypeC_de_results.csv", index=False)
        
        yield root
        
        # Cleanup handled by TemporaryDirectory

@pytest.fixture
def temp_project_empty_intersection():
    """Create a structure where intersection is empty (triggers fallback)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        processed_dir = root / "data" / "processed"
        results_dir = root / "results"
        meta_dir = results_dir / "meta_analysis"
        
        processed_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)
        meta_dir.mkdir(parents=True, exist_ok=True)
        
        # Type A: Genes 1, 2
        # Type B: Genes 3, 4
        # Type C: Genes 5, 6
        # Intersection: Empty
        
        data_a = {
            'gene': ['GENE1', 'GENE2'],
            'pvalue': [0.01, 0.02],
            'log2FC': [2.0, 1.5],
            'significant': [True, True]
        }
        pd.DataFrame(data_a).to_csv(processed_dir / "loo_iteration_TypeA_de_results.csv", index=False)
        
        data_b = {
            'gene': ['GENE3', 'GENE4'],
            'pvalue': [0.01, 0.02],
            'log2FC': [1.5, 2.0],
            'significant': [True, True]
        }
        pd.DataFrame(data_b).to_csv(processed_dir / "loo_iteration_TypeB_de_results.csv", index=False)
        
        data_c = {
            'gene': ['GENE5', 'GENE6'],
            'pvalue': [0.01, 0.02],
            'log2FC': [1.2, 1.5],
            'significant': [True, True]
        }
        pd.DataFrame(data_c).to_csv(processed_dir / "loo_iteration_TypeC_de_results.csv", index=False)
        
        yield root

@pytest.fixture
def temp_project_top_ranked():
    """Create a structure for testing top-ranked union logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        processed_dir = root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Type A: G1 (p=0.01), G2 (p=0.05)
        # Type B: G1 (p=0.02), G3 (p=0.01)
        # Type C: G1 (p=0.01), G4 (p=0.01)
        # G1 appears 3 times (should be top)
        
        data_a = {
            'gene': ['G1', 'G2'],
            'pvalue': [0.01, 0.05],
            'log2FC': [2.0, 1.5],
            'significant': [True, True]
        }
        pd.DataFrame(data_a).to_csv(processed_dir / "loo_iteration_TypeA_de_results.csv", index=False)
        
        data_b = {
            'gene': ['G1', 'G3'],
            'pvalue': [0.02, 0.01],
            'log2FC': [1.5, 2.0],
            'significant': [True, True]
        }
        pd.DataFrame(data_b).to_csv(processed_dir / "loo_iteration_TypeB_de_results.csv", index=False)
        
        data_c = {
            'gene': ['G1', 'G4'],
            'pvalue': [0.01, 0.01],
            'log2FC': [1.2, 1.5],
            'significant': [True, True]
        }
        pd.DataFrame(data_c).to_csv(processed_dir / "loo_iteration_TypeC_de_results.csv", index=False)
        
        yield root

class TestLoadDiscoveryResults:
    def test_load_discovery_set_valid(self, temp_project_structure):
        processed_dir = temp_project_structure / "data" / "processed"
        results = load_discovery_results(processed_dir)
        
        assert len(results) == 3
        assert "TypeA" in results
        assert "TypeB" in results
        assert "TypeC" in results
        
        # Check significant genes
        assert "GENE1" in results["TypeA"]
        assert "GENE2" in results["TypeA"]
        assert "GENE3" in results["TypeA"]
        assert "GENE_X" not in results["TypeA"]

class TestComputeIntersection:
    def test_compute_intersection_valid(self, temp_project_structure):
        processed_dir = temp_project_structure / "data" / "processed"
        results = load_discovery_results(processed_dir)
        intersection = compute_intersection(results)
        
        # Only GENE3 is in all three
        assert intersection == {"GENE3"}

    def test_compute_intersection_empty(self, temp_project_empty_intersection):
        processed_dir = temp_project_empty_intersection / "data" / "processed"
        results = load_discovery_results(processed_dir)
        intersection = compute_intersection(results)
        
        assert intersection == set()

class TestComputeUnionTopRanked:
    def test_union_top_ranked_logic(self, temp_project_top_ranked):
        processed_dir = temp_project_top_ranked / "data" / "processed"
        results = load_discovery_results(processed_dir)
        
        # G1 appears 3 times, others 1 time. G1 should be first.
        union_genes = compute_union_top_ranked(results, limit=50, processed_dir=processed_dir)
        
        assert len(union_genes) >= 1
        assert union_genes[0] == "G1", f"Expected G1 first, got {union_genes[0]}"

class TestSaveGenePanel:
    def test_save_gene_panel(self, temp_project_structure):
        panel_path = temp_project_structure / "results" / "meta_analysis" / "gene_panel.json"
        genes = ["GENE1", "GENE2"]
        
        save_gene_panel(genes, panel_path)
        
        assert panel_path.exists()
        with open(panel_path) as f:
            data = json.load(f)
        
        assert data["selected"] == genes
        assert data["count"] == 2
        assert data["method"] == "intersection"

class TestAggregateAndSelectPanel:
    def test_fallback_triggered(self, temp_project_empty_intersection):
        root = temp_project_empty_intersection
        processed_dir = root / "data" / "processed"
        summary_path = root / "results" / "summary.md"
        panel_path = root / "results" / "meta_analysis" / "gene_panel.json"
        
        result = aggregate_and_select_panel(
            processed_dir=processed_dir,
            summary_path=summary_path,
            panel_path=panel_path
        )
        
        assert result["status"] == "success"
        assert result["method"] == "union_top_ranked"
        assert result["fallback_reason"] == "intersection_empty"
        
        # Check summary.md was updated
        assert summary_path.exists()
        content = summary_path.read_text()
        assert "fallback_reason: \"intersection_empty\"" in content
        
        # Check panel saved
        assert panel_path.exists()
        with open(panel_path) as f:
            panel_data = json.load(f)
        assert panel_data["fallback_reason"] == "intersection_empty"

    def test_intersection_success(self, temp_project_structure):
        root = temp_project_structure
        processed_dir = root / "data" / "processed"
        summary_path = root / "results" / "summary.md"
        panel_path = root / "results" / "meta_analysis" / "gene_panel.json"
        
        result = aggregate_and_select_panel(
            processed_dir=processed_dir,
            summary_path=summary_path,
            panel_path=panel_path
        )
        
        assert result["status"] == "success"
        assert result["method"] == "intersection"
        assert result["fallback_reason"] is None
        
        # Check panel saved
        with open(panel_path) as f:
            panel_data = json.load(f)
        assert panel_data["selected"] == ["GENE3"]
        assert panel_data["count"] == 1