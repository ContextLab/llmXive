"""
Unit tests for meta-analysis functions.
Tests the intersection and union logic for biomarker panel selection.
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
    load_discovery_results,
    save_gene_panel
)

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure with mock discovery results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create necessary directories
        data_processed = tmpdir_path / "data" / "processed"
        results_meta = tmpdir_path / "results" / "meta_analysis"
        data_processed.mkdir(parents=True, exist_ok=True)
        results_meta.mkdir(parents=True, exist_ok=True)
        
        # Create mock discovery results for 3 tumor types
        tumor_types = ["BRCA", "LUAD", "COAD"]
        
        # Mock data: Some genes overlap, some don't
        gene_data = {
            "BRCA": {
                "significant_genes": ["GENE_A", "GENE_B", "GENE_C", "GENE_D"]
            },
            "LUAD": {
                "significant_genes": ["GENE_A", "GENE_B", "GENE_E", "GENE_F"]
            },
            "COAD": {
                "significant_genes": ["GENE_A", "GENE_B", "GENE_G"]
            }
        }
        
        for tt, data in gene_data.items():
            results_file = data_processed / f"{tt}_discovery_de_results.json"
            with open(results_file, 'w') as f:
                json.dump(data, f)
        
        yield tmpdir_path, data_processed, results_meta

@pytest.fixture
def temp_project_empty_intersection():
    """Create a temporary project structure where intersection is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        data_processed = tmpdir_path / "data" / "processed"
        results_meta = tmpdir_path / "results" / "meta_analysis"
        data_processed.mkdir(parents=True, exist_ok=True)
        results_meta.mkdir(parents=True, exist_ok=True)
        
        # No overlapping genes
        gene_data = {
            "BRCA": {
                "significant_genes": ["GENE_A", "GENE_B", "GENE_C"]
            },
            "LUAD": {
                "significant_genes": ["GENE_D", "GENE_E", "GENE_F"]
            },
            "COAD": {
                "significant_genes": ["GENE_G", "GENE_H", "GENE_I"]
            }
        }
        
        for tt, data in gene_data.items():
            results_file = data_processed / f"{tt}_discovery_de_results.json"
            with open(results_file, 'w') as f:
                json.dump(data, f)
        
        yield tmpdir_path, data_processed, results_meta

@pytest.fixture
def temp_project_top_ranked():
    """Create a temporary project structure for union top-ranked test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        data_processed = tmpdir_path / "data" / "processed"
        results_meta = tmpdir_path / "results" / "meta_analysis"
        data_processed.mkdir(parents=True, exist_ok=True)
        results_meta.mkdir(parents=True, exist_ok=True)
        
        # Mock data with ranking information
        gene_data = {
            "BRCA": {
                "significant_genes": [
                    {"gene": "GENE_A", "pvalue": 1e-10, "log2fc": 2.5},
                    {"gene": "GENE_B", "pvalue": 1e-8, "log2fc": 2.0},
                    {"gene": "GENE_C", "pvalue": 1e-6, "log2fc": 1.5}
                ]
            },
            "LUAD": {
                "significant_genes": [
                    {"gene": "GENE_D", "pvalue": 1e-9, "log2fc": 2.2},
                    {"gene": "GENE_E", "pvalue": 1e-7, "log2fc": 1.8},
                    {"gene": "GENE_F", "pvalue": 1e-5, "log2fc": 1.2}
                ]
            }
        }
        
        for tt, data in gene_data.items():
            results_file = data_processed / f"{tt}_discovery_de_results.json"
            with open(results_file, 'w') as f:
                json.dump(data, f)
        
        yield tmpdir_path, data_processed, results_meta

class TestComputeIntersection:
    """Tests for compute_intersection function."""

    def test_intersection_basic(self, temp_project_structure):
        """Test basic intersection computation with overlapping genes."""
        tmpdir_path, _, _ = temp_project_structure
        
        result = compute_intersection(["BRCA", "LUAD", "COAD"], tmpdir_path)
        
        # Expected: GENE_A and GENE_B are in all three
        assert len(result) == 2
        assert "GENE_A" in result
        assert "GENE_B" in result
        assert "GENE_C" not in result

    def test_intersection_two_types(self, temp_project_structure):
        """Test intersection with exactly two tumor types."""
        tmpdir_path, _, _ = temp_project_structure
        
        result = compute_intersection(["BRCA", "LUAD"], tmpdir_path)
        
        # Expected: GENE_A and GENE_B are in both
        assert len(result) == 2
        assert "GENE_A" in result
        assert "GENE_B" in result

    def test_intersection_empty(self, temp_project_empty_intersection):
        """Test intersection when no genes overlap."""
        tmpdir_path, _, _ = temp_project_empty_intersection
        
        result = compute_intersection(["BRCA", "LUAD", "COAD"], tmpdir_path)
        
        assert len(result) == 0
        assert result == []

    def test_intersection_insufficient_types(self, temp_project_structure):
        """Test that intersection requires at least 2 tumor types."""
        tmpdir_path, _, _ = temp_project_structure
        
        with pytest.raises(ValueError) as excinfo:
            compute_intersection(["BRCA"], tmpdir_path)
        
        assert "at least 2 tumor types" in str(excinfo.value)

    def test_intersection_missing_file(self, temp_project_structure):
        """Test that intersection raises error for missing tumor type."""
        tmpdir_path, _, _ = temp_project_structure
        
        with pytest.raises(FileNotFoundError):
            compute_intersection(["BRCA", "LUAD", "MISSING"], tmpdir_path)

class TestComputeUnionTopRanked:
    """Tests for compute_union_top_ranked function."""

    def test_union_basic(self, temp_project_top_ranked):
        """Test union of top-ranked genes."""
        tmpdir_path, _, _ = temp_project_top_ranked
        
        result = compute_union_top_ranked(["BRCA", "LUAD"], tmpdir_path, max_genes=2)
        
        # Should have top 2 from each: GENE_A, GENE_B from BRCA; GENE_D, GENE_E from LUAD
        assert len(result) == 4
        assert "GENE_A" in result
        assert "GENE_B" in result
        assert "GENE_D" in result
        assert "GENE_E" in result

    def test_union_max_genes_limit(self, temp_project_top_ranked):
        """Test that max_genes parameter limits the number of genes per type."""
        tmpdir_path, _, _ = temp_project_top_ranked
        
        result = compute_union_top_ranked(["BRCA", "LUAD"], tmpdir_path, max_genes=1)
        
        # Should have top 1 from each: GENE_A from BRCA; GENE_D from LUAD
        assert len(result) == 2
        assert "GENE_A" in result
        assert "GENE_D" in result

    def test_union_handles_missing_file(self, temp_project_top_ranked):
        """Test that union gracefully handles missing tumor types."""
        tmpdir_path, _, _ = temp_project_top_ranked
        
        # Should not raise, just skip missing type
        result = compute_union_top_ranked(["BRCA", "MISSING"], tmpdir_path, max_genes=2)
        
        # Should still get genes from BRCA
        assert len(result) == 2

class TestSaveGenePanel:
    """Tests for save_gene_panel function."""

    def test_save_panel_intersection(self, temp_project_structure):
        """Test saving a gene panel with intersection method."""
        _, _, results_meta = temp_project_structure
        output_path = results_meta / "test_panel.json"
        
        genes = ["GENE_A", "GENE_B"]
        save_gene_panel(genes, output_path, intersection_used=True)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["genes"] == genes
        assert data["panel_size"] == len(genes)
        assert data["method"] == "intersection"
        assert data["fallback_reason"] is None

    def test_save_panel_fallback(self, temp_project_empty_intersection):
        """Test saving a gene panel with fallback method."""
        _, _, results_meta = temp_project_empty_intersection
        output_path = results_meta / "test_panel.json"
        
        genes = ["GENE_A", "GENE_B"]
        save_gene_panel(genes, output_path, intersection_used=False, 
                       fallback_reason="intersection_empty")
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["genes"] == genes
        assert data["panel_size"] == len(genes)
        assert data["method"] == "union_fallback"
        assert data["fallback_reason"] == "intersection_empty"

class TestLoadDiscoveryResults:
    """Tests for load_discovery_results function."""

    def test_load_valid_results(self, temp_project_structure):
        """Test loading valid discovery results."""
        tmpdir_path, _, _ = temp_project_structure
        
        result = load_discovery_results("BRCA", tmpdir_path)
        
        assert "significant_genes" in result
        assert len(result["significant_genes"]) == 4

    def test_load_missing_file(self, temp_project_structure):
        """Test that loading missing file raises error."""
        tmpdir_path, _, _ = temp_project_structure
        
        with pytest.raises(FileNotFoundError):
            load_discovery_results("MISSING", tmpdir_path)

    def test_load_invalid_json(self, temp_project_structure):
        """Test that loading invalid JSON raises error."""
        tmpdir_path, data_processed, _ = temp_project_structure
        
        # Create invalid JSON file
        invalid_file = data_processed / "INVALID_discovery_de_results.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(ValueError):
            load_discovery_results("INVALID", tmpdir_path)

    def test_load_missing_key(self, temp_project_structure):
        """Test that loading file without required key raises error."""
        tmpdir_path, data_processed, _ = temp_project_structure
        
        # Create file without significant_genes key
        invalid_file = data_processed / "MISSINGKEY_discovery_de_results.json"
        with open(invalid_file, 'w') as f:
            json.dump({"other_key": "value"}, f)
        
        with pytest.raises(ValueError):
            load_discovery_results("MISSINGKEY", tmpdir_path)
