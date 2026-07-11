"""
Unit tests for the Report Generation module (T033).
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Ensure src is in path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.report_generator import (
    generate_final_report,
    ReportGenerationError,
    load_precomputed_anova_results,
    load_retention_comparison_results
)


class TestReportGenerator:
    
    def setup_method(self):
        """Set up temporary directories and mock data for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        
        # Create mock statistical analysis results
        self.anova_data = {
            "forgetting_analysis": {
                "mean_forgetting_sequential": 0.15,
                "mean_forgetting_mixed": 0.12,
                "mean_forgetting_coevolving": 0.05
            },
            "anova_results": {
                "f_statistic": 12.45,
                "p_value": 0.0003,
                "degrees_of_freedom": [2, 87]
            },
            "tukey_results": {
                "significant_pairs": [("coevolving", "mixed"), ("coevolving", "sequential")],
                "p_values": {"coevolving_mixed": 0.01, "coevolving_sequential": 0.001}
            },
            "descriptive_statistics": {
                "total_runs": 30,
                "conditions": ["sequential", "mixed", "coevolving"]
            },
            "total_runs_analyzed": 30,
            "significant_forgetting_detected": True
        }

        # Create mock retention comparison results
        self.retention_data = {
            "retention_comparison": {
                "coevolving_mean": 0.95,
                "mixed_mean": 0.88,
                "difference": 0.07,
                "p_value": 0.02
            },
            "coevolving_better_than_mixed": True,
            "statistical_significance": True
        }

        # Write mock files
        self.anova_path = self.data_dir / "statistical_analysis_results.json"
        self.retention_path = self.data_dir / "retention_comparison_results.json"
        self.forgetting_path = self.data_dir / "forgetting_metrics_data.json"
        self.output_path = self.data_dir / "forgetting_analysis.json"

        with open(self.anova_path, 'w') as f:
            json.dump(self.anova_data, f)
        
        with open(self.retention_path, 'w') as f:
            json.dump(self.retention_data, f)
        
        # Empty forgetting data for this test
        with open(self.forgetting_path, 'w') as f:
            json.dump({}, f)

    def test_load_precomputed_anova_results(self):
        """Test loading ANOVA results from a valid file."""
        result = load_precomputed_anova_results(self.anova_path)
        assert result["anova_results"]["p_value"] == 0.0003
        assert "forgetting_analysis" in result

    def test_load_precomputed_anova_results_missing_file(self):
        """Test that missing file raises ReportGenerationError."""
        with pytest.raises(ReportGenerationError):
            load_precomputed_anova_results(self.data_dir / "nonexistent.json")

    def test_load_retention_comparison_results(self):
        """Test loading retention results from a valid file."""
        result = load_retention_comparison_results(self.retention_path)
        assert result["coevolving_better_than_mixed"] is True

    def test_generate_final_report(self):
        """Test the full report generation pipeline."""
        report = generate_final_report(
            forgetting_data_path=self.forgetting_path,
            retention_data_path=self.retention_path,
            output_path=self.output_path
        )

        assert self.output_path.exists()
        assert report["summary"]["total_runs_analyzed"] == 30
        assert report["summary"]["significant_forgetting_detected"] is True
        assert report["summary"]["coevolving_better_than_mixed"] is True
        assert "key_finding" in report["summary"]
        assert "p < 0.05" in report["summary"]["key_finding"]

    def test_generate_final_report_missing_anova(self):
        """Test that missing ANOVA file raises ReportGenerationError."""
        # Remove the ANOVA file
        self.anova_path.unlink()
        
        with pytest.raises(ReportGenerationError) as exc_info:
            generate_final_report(
                forgetting_data_path=self.forgetting_path,
                retention_data_path=self.retention_path,
                output_path=self.output_path
            )
        
        assert "statistical analysis results not found" in str(exc_info.value).lower()

    def test_generate_final_report_missing_retention(self):
        """Test that missing retention file raises ReportGenerationError."""
        # Remove the retention file
        self.retention_path.unlink()
        
        with pytest.raises(ReportGenerationError) as exc_info:
            generate_final_report(
                forgetting_data_path=self.forgetting_path,
                retention_data_path=self.retention_path,
                output_path=self.output_path
            )
        
        assert "retention comparison results not found" in str(exc_info.value).lower()

    def test_report_schema_validity(self):
        """Test that the generated report adheres to the expected schema."""
        report = generate_final_report(
            forgetting_data_path=self.forgetting_path,
            retention_data_path=self.retention_path,
            output_path=self.output_path
        )

        required_keys = [
            "report_metadata",
            "forgetting_analysis",
            "anova_results",
            "tukey_results",
            "retention_comparison",
            "descriptive_statistics",
            "summary"
        ]

        for key in required_keys:
            assert key in report, f"Missing required key: {key}"

        summary_keys = ["total_runs_analyzed", "significant_forgetting_detected", "coevolving_better_than_mixed", "key_finding"]
        for key in summary_keys:
            assert key in report["summary"], f"Missing summary key: {key}"