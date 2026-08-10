"""
Unit tests for modeling module, including T025 (pathway mapping logic) and T026 (interpretation).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.modeling.interpret import (
    map_metabolite_to_pathways,
    get_mean_abs_shap,
    generate_biological_report
)
from code.modeling.train import train_model
from code.modeling.evaluate import compute_metrics


class TestPathwayMapping:
    """Tests for T025: Unit test for pathway mapping logic."""

    def test_map_metabolite_to_pathways_empty_inchikey(self):
        """Test that empty InChIKey returns empty list."""
        result = map_metabolite_to_pathways("")
        assert result == []

    def test_map_metabolite_to_pathways_none_inchikey(self):
        """Test that None InChIKey returns empty list."""
        result = map_metabolite_to_pathways(None)
        assert result == []

    def test_map_metabolite_to_pathways_valid_format(self):
        """Test that a valid InChIKey format returns a list (may be empty if not in KEGG)."""
        # Use a known InChIKey format (not necessarily in KEGG)
        inchikey = "InChIKey=1S/C16H10O6/c17-13-9-5-1-3-7-11(9)15(19)16-12-8-4-2-6-10(14(16)20)18-13/h1-8,17-18H"
        result = map_metabolite_to_pathways(inchikey)
        assert isinstance(result, list)
        # The result may be empty if the metabolite is not in KEGG, but the function should not crash

    def test_map_metabolite_to_pathways_return_structure(self):
        """Test that returned pathways have expected structure."""
        # Test with a real InChIKey for quercetin (common plant metabolite)
        quercetin_inchikey = "QORWJWZARLRLPR-UHFFFAOYSA-H"
        result = map_metabolite_to_pathways(quercetin_inchikey)
        
        if result:  # If pathways were found
            for pathway in result:
                assert "pathway_id" in pathway
                assert "compound_id" in pathway
                assert "inchikey" in pathway


class TestSHAPAnalysis:
    """Tests for SHAP-related functions."""

    def test_get_mean_abs_shap(self):
        """Test calculation of mean absolute SHAP values."""
        # Create mock SHAP data
        np.random.seed(42)
        n_samples, n_features = 100, 10
        shap_values = np.random.randn(n_samples, n_features)
        columns = [f"feature_{i}" for i in range(n_features)]
        shap_df = pd.DataFrame(shap_values, columns=columns)

        result = get_mean_abs_shap(shap_df)

        assert isinstance(result, pd.Series)
        assert len(result) == n_features
        assert all(result >= 0)  # Mean absolute values should be non-negative
        assert result.index.equals(shap_df.columns)

    def test_get_mean_abs_shap_sorted(self):
        """Test that mean absolute SHAP values are sorted in descending order."""
        np.random.seed(42)
        n_samples, n_features = 50, 5
        shap_values = np.random.randn(n_samples, n_features)
        columns = [f"feature_{i}" for i in range(n_features)]
        shap_df = pd.DataFrame(shap_values, columns=columns)

        result = get_mean_abs_shap(shap_df)

        # Check that values are sorted descending
        assert result.is_monotonic_decreasing


class TestBiologicalReport:
    """Tests for biological report generation."""

    def test_generate_biological_report_structure(self):
        """Test that the generated report has expected structure."""
        # Create mock data
        shap_summary = pd.Series(
            [0.5, 0.3, 0.2, 0.1, 0.05],
            index=["metabolite_A", "metabolite_B", "metabolite_C", "metabolite_D", "metabolite_E"]
        )
        
        metabolite_info = pd.DataFrame([
            {
                "metabolite_name": "metabolite_A",
                "inchikey": "TEST123",
                "pathway_count": 2,
                "pathways": [{"pathway_id": "P001"}, {"pathway_id": "P002"}]
            },
            {
                "metabolite_name": "metabolite_B",
                "inchikey": "TEST456",
                "pathway_count": 1,
                "pathways": [{"pathway_id": "P003"}]
            },
            {
                "metabolite_name": "metabolite_C",
                "inchikey": "TEST789",
                "pathway_count": 0,
                "pathways": []
            },
            {
                "metabolite_name": "metabolite_D",
                "inchikey": "TEST101",
                "pathway_count": 3,
                "pathways": [{"pathway_id": "P004"}, {"pathway_id": "P005"}, {"pathway_id": "P006"}]
            },
            {
                "metabolite_name": "metabolite_E",
                "inchikey": "TEST102",
                "pathway_count": 0,
                "pathways": []
            }
        ])

        report = generate_biological_report(shap_summary, metabolite_info, top_n=3)

        assert isinstance(report, str)
        assert "Biological Interpretation Report" in report
        assert "Top Metabolites by SHAP Importance" in report
        assert "Biological Plausibility Discussion" in report
        assert "metabolite_A" in report
        assert "metabolite_B" in report
        assert "metabolite_C" in report
        assert "P001" in report or "P002" in report  # Pathways should be mentioned

    def test_generate_biological_report_top_n(self):
        """Test that only top_n metabolites are included in the report."""
        shap_summary = pd.Series(
            [0.5, 0.3, 0.2, 0.1, 0.05],
            index=["metabolite_A", "metabolite_B", "metabolite_C", "metabolite_D", "metabolite_E"]
        )
        
        metabolite_info = pd.DataFrame([
            {"metabolite_name": "metabolite_A", "inchikey": "A", "pathway_count": 0, "pathways": []},
            {"metabolite_name": "metabolite_B", "inchikey": "B", "pathway_count": 0, "pathways": []},
            {"metabolite_name": "metabolite_C", "inchikey": "C", "pathway_count": 0, "pathways": []},
            {"metabolite_name": "metabolite_D", "inchikey": "D", "pathway_count": 0, "pathways": []},
            {"metabolite_name": "metabolite_E", "inchikey": "E", "pathway_count": 0, "pathways": []}
        ])

        # Test with top_n=2
        report = generate_biological_report(shap_summary, metabolite_info, top_n=2)

        assert "metabolite_A" in report
        assert "metabolite_B" in report
        assert "metabolite_C" not in report  # Should not be in top 2
        assert "metabolite_D" not in report
        assert "metabolite_E" not in report


class TestIntegration:
    """Integration tests for the full interpretation pipeline."""

    def test_full_pipeline_structure(self):
        """Test that the full pipeline produces expected output files."""
        # This test checks the structure without running the full pipeline
        # (which requires trained models and data)
        
        from code.modeling.interpret import (
            SHAP_OUTPUT_FILE,
            PATHWAY_OUTPUT_FILE,
            REPORT_OUTPUT_FILE
        )
        
        assert SHAP_OUTPUT_FILE.name == "shap_analysis.json"
        assert PATHWAY_OUTPUT_FILE.name == "pathway_analysis.json"
        assert REPORT_OUTPUT_FILE.name == "biological_interpretation_report.md"
        assert str(SHAP_OUTPUT_FILE).startswith("results/")
        assert str(PATHWAY_OUTPUT_FILE).startswith("results/")
        assert str(REPORT_OUTPUT_FILE).startswith("results/")