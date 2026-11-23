"""
Unit tests for the associational report generation functionality.

Tests verify that all findings are properly framed as ASSOCIATIONAL
as required by FR-011.
"""
import pytest
import json
import os
from pathlib import Path
import sys
from datetime import datetime

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.generate_associational_report import (
    generate_associational_report,
    load_json_file
)

class TestAssociationalReport:
    """Test cases for associational report generation."""
    
    def test_report_contains_disclaimer(self):
        """Test that the report contains the required associational disclaimer."""
        report = generate_associational_report()
        
        assert "disclaimer" in report
        assert "ASSOCIATIONAL" in report["disclaimer"]
        assert "causal" in report["disclaimer"].lower()
        
    def test_report_contains_methodology_note(self):
        """Test that the report contains methodology notes about observational nature."""
        report = generate_associational_report()
        
        assert "methodology_note" in report
        assert "observational" in report["methodology_note"].lower()
        assert "causality" in report["methodology_note"].lower()
        
    def test_report_contains_limitations(self):
        """Test that the report includes appropriate limitations."""
        report = generate_associational_report()
        
        assert "limitations" in report
        assert len(report["limitations"]) > 0
        
        # Check that causal limitations are mentioned
        limitations_text = " ".join(report["limitations"]).lower()
        assert "causal" in limitations_text or "confounding" in limitations_text
        
    def test_report_contains_recommendations(self):
        """Test that the report includes recommendations for experimental validation."""
        report = generate_associational_report()
        
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0
        
        # Check that validation recommendations are present
        recommendations_text = " ".join(report["recommendations"]).lower()
        assert "experimental" in recommendations_text or "validation" in recommendations_text
        
    def test_feature_associations_use_associational_language(self):
        """Test that feature associations are framed as associational."""
        mock_shap_data = {
            "top_features": [
                {"name": "Test_Metabolite", "value": 0.5, "importance": "high"}
            ]
        }
        
        report = generate_associational_report(shap_data=mock_shap_data)
        
        assert len(report["findings"]["feature_associations"]) > 0
        feature_interp = report["findings"]["feature_associations"][0]["interpretation"]
        
        assert "ASSOCIATION" in feature_interp or "association" in feature_interp
        assert "causal" not in feature_interp.lower() or "not causal" in feature_interp.lower()
        
    def test_pathway_associations_use_associational_language(self):
        """Test that pathway associations are framed as associational."""
        mock_pathway_data = {
            "pathways": [
                {"name": "Test_Pathway", "id": "TEST001", "score": 0.8, "metabolite_count": 5}
            ]
        }
        
        report = generate_associational_report(pathway_data=mock_pathway_data)
        
        assert len(report["findings"]["pathway_associations"]) > 0
        pathway_interp = report["findings"]["pathway_associations"][0]["interpretation"]
        
        assert "ASSOCIATIONAL" in pathway_interp or "association" in pathway_interp
        assert "causal" not in pathway_interp.lower() or "not causal" in pathway_interp.lower()
        
    def test_model_performance_interpretation_is_associational(self):
        """Test that model performance interpretation is framed as associational."""
        mock_metrics_data = {
            "balanced_accuracy": 0.85,
            "roc_auc": 0.90,
            "precision_recall": 0.88
        }
        
        report = generate_associational_report(metrics_data=mock_metrics_data)
        
        assert "model_performance" in report["findings"]
        perf_interp = report["findings"]["model_performance"]["interpretation"]
        
        assert "ASSOCIATIONAL" in perf_interp or "association" in perf_interp
        assert "causal" not in perf_interp.lower() or "not causal" in perf_interp.lower()
        
    def test_report_type_is_correct(self):
        """Test that the report type is correctly identified."""
        report = generate_associational_report()
        
        assert report["report_type"] == "ASSOCIATIONAL_FINDINGS"
        
    def test_report_contains_timestamp(self):
        """Test that the report contains a generation timestamp."""
        report = generate_associational_report()
        
        assert "generation_timestamp" in report
        # Try to parse the timestamp to ensure it's valid
        datetime.fromisoformat(report["generation_timestamp"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])