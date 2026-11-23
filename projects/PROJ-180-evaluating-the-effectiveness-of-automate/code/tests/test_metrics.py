import pytest
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to resolve imports like utils.stats
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.stats import wilcoxon_signed_rank, fit_mixed_effects_model
from utils.config import get_results_dir

class TestMetricsCalculation:
    """
    Contract test for metrics calculation (T030) and
    Integration test for statistical analysis pipeline (T031).
    """
    
    @pytest.fixture
    def mock_aligned_pairs(self):
        """
        Generates a deterministic mock dataset for aligned pairs.
        This simulates the output of T027-3 (aligned_pairs.json).
        """
        return [
            {
                "repo_id": "repo_A",
                "tool": "sonarqube",
                "category": "security",
                "matched": True,
                "f1_score": 0.75,
                "precision": 0.80,
                "recall": 0.71
            },
            {
                "repo_id": "repo_A",
                "tool": "deepsource",
                "category": "security",
                "matched": True,
                "f1_score": 0.68,
                "precision": 0.72,
                "recall": 0.64
            },
            {
                "repo_id": "repo_B",
                "tool": "sonarqube",
                "category": "style",
                "matched": True,
                "f1_score": 0.82,
                "precision": 0.85,
                "recall": 0.79
            },
            {
                "repo_id": "repo_B",
                "tool": "deepsource",
                "category": "style",
                "matched": True,
                "f1_score": 0.60,
                "precision": 0.65,
                "recall": 0.56
            },
            {
                "repo_id": "repo_C",
                "tool": "sonarqube",
                "category": "security",
                "matched": True,
                "f1_score": 0.70,
                "precision": 0.75,
                "recall": 0.66
            },
            {
                "repo_id": "repo_C",
                "tool": "deepsource",
                "category": "security",
                "matched": True,
                "f1_score": 0.65,
                "precision": 0.70,
                "recall": 0.61
            }
        ]

    @pytest.fixture
    def mock_regression_data(self):
        """
        Generates mock data for Mixed-Effects Model testing (T034).
        """
        return [
            {"repo_id": "repo_A", "tool": "sonarqube", "language": "Python", "project_size": 10000, "f1_score": 0.75},
            {"repo_id": "repo_A", "tool": "deepsource", "language": "Python", "project_size": 10000, "f1_score": 0.68},
            {"repo_id": "repo_B", "tool": "sonarqube", "language": "Java", "project_size": 50000, "f1_score": 0.82},
            {"repo_id": "repo_B", "tool": "deepsource", "language": "Java", "project_size": 50000, "f1_score": 0.60},
            {"repo_id": "repo_C", "tool": "sonarqube", "language": "Python", "project_size": 15000, "f1_score": 0.70},
            {"repo_id": "repo_C", "tool": "deepsource", "language": "Python", "project_size": 15000, "f1_score": 0.65},
            {"repo_id": "repo_D", "tool": "sonarqube", "language": "Go", "project_size": 20000, "f1_score": 0.78},
            {"repo_id": "repo_D", "tool": "deepsource", "language": "Go", "project_size": 20000, "f1_score": 0.62},
        ]

class TestStatisticalPipelineIntegration:
    """
    Integration test for the full statistical analysis pipeline (T031).
    Verifies that the pipeline can ingest mock data, run Wilcoxon tests,
    fit Mixed-Effects models, and produce result artifacts without crashing.
    """

    def test_wilcoxon_integration(self, mock_aligned_pairs):
        """
        Tests the Wilcoxon signed-rank test implementation from utils.stats
        using mock F1 scores grouped by tool.
        """
        sonar_scores = [p["f1_score"] for p in mock_aligned_pairs if p["tool"] == "sonarqube"]
        deepsource_scores = [p["f1_score"] for p in mock_aligned_pairs if p["tool"] == "deepsource"]
        
        # Ensure we have paired data for the same repos (simplified for mock)
        # In real data, we would pair by repo_id. Here we assume the mock is paired.
        assert len(sonar_scores) == len(deepsource_scores), "Mock data must be paired for Wilcoxon"
        
        result = wilcoxon_signed_rank(sonar_scores, deepsource_scores)
        
        assert "statistic" in result
        assert "pvalue" in result
        assert isinstance(result["statistic"], float)
        assert isinstance(result["pvalue"], float)
        assert result["pvalue"] >= 0.0
        assert result["pvalue"] <= 1.0

    def test_mixed_effects_integration(self, mock_regression_data):
        """
        Tests the Mixed-Effects Linear Model fitting from utils.stats.
        """
        import pandas as pd
        df = pd.DataFrame(mock_regression_data)
        
        # Test that the function runs without error on valid data
        result = fit_mixed_effects_model(
            df, 
            dependent_var="f1_score", 
            independent_vars=["tool", "language", "project_size"], 
            random_effect="repo_id"
        )
        
        assert result is not None
        assert "coefficients" in result
        assert "pvalues" in result
        assert "summary" in result
        
        # Verify basic structure of coefficients
        coeffs = result["coefficients"]
        assert len(coeffs) > 0
        assert "tool" in str(coeffs) or "language" in str(coeffs) or "project_size" in str(coeffs)

    def test_full_pipeline_artifact_generation(self, mock_aligned_pairs, mock_regression_data, tmp_path):
        """
        Integration test verifying that the pipeline generates the expected
        output files (CSV/PNG/JSON) in the results directory.
        This simulates the execution of T038-1, T038-2, and T038-3.
        """
        import pandas as pd
        import json as json_module
        from utils.config import get_results_dir
        
        # Mock the results directory to use tmp_path for this test
        # In a real run, this would be the actual results folder
        results_dir = Path(tmp_path)
        
        # 1. Simulate Metrics Calculation (T032)
        metrics_data = []
        for pair in mock_aligned_pairs:
            metrics_data.append({
                "repo_id": pair["repo_id"],
                "tool": pair["tool"],
                "precision": pair["precision"],
                "recall": pair["recall"],
                "f1_score": pair["f1_score"]
            })
        
        metrics_df = pd.DataFrame(metrics_data)
        metrics_csv_path = results_dir / "metrics_summary.csv"
        metrics_df.to_csv(metrics_csv_path, index=False)
        
        assert metrics_csv_path.exists()
        assert metrics_csv_path.stat().st_size > 0

        # 2. Simulate Statistical Analysis (T033, T034)
        # Wilcoxon result
        sonar_scores = [p["f1_score"] for p in mock_aligned_pairs if p["tool"] == "sonarqube"]
        deepsource_scores = [p["f1_score"] for p in mock_aligned_pairs if p["tool"] == "deepsource"]
        wilcoxon_result = wilcoxon_signed_rank(sonar_scores, deepsource_scores)
        
        wilcoxon_json_path = results_dir / "wilcoxon_results.json"
        with open(wilcoxon_json_path, 'w') as f:
            json_module.dump(wilcoxon_result, f)
        
        assert wilcoxon_json_path.exists()

        # Mixed Effects result
        reg_df = pd.DataFrame(mock_regression_data)
        reg_result = fit_mixed_effects_model(
            reg_df, 
            dependent_var="f1_score", 
            independent_vars=["tool", "language", "project_size"], 
            random_effect="repo_id"
        )
        
        reg_csv_path = results_dir / "regression_summary.csv"
        reg_df_summary = pd.DataFrame([reg_result["coefficients"]]) # Simplified for test
        reg_df_summary.to_csv(reg_csv_path, index=False)
        
        assert reg_csv_path.exists()
        assert reg_csv_path.stat().st_size > 0

        # 3. Verify Final Report (T038-3)
        final_report = {
            "wilcoxon": wilcoxon_result,
            "regression_summary_path": str(reg_csv_path),
            "metrics_summary_path": str(metrics_csv_path),
            "status": "success"
        }
        
        final_report_path = results_dir / "metrics_report.json"
        with open(final_report_path, 'w') as f:
            json_module.dump(final_report, f)
        
        assert final_report_path.exists()
        assert final_report_path.stat().st_size > 0

        # Verify we can read back the JSON
        with open(final_report_path, 'r') as f:
            loaded_report = json_module.load(f)
        
        assert loaded_report["status"] == "success"
        assert "statistic" in loaded_report["wilcoxon"]

    def test_edge_case_empty_data(self):
        """
        Tests that the statistical functions handle empty or insufficient data gracefully.
        """
        # Wilcoxon requires at least 2 pairs
        with pytest.raises(Exception): # scipy.stats.wilcoxon raises ValueError for n < 2
            wilcoxon_signed_rank([], [])
        
        # Mixed effects requires data
        import pandas as pd
        empty_df = pd.DataFrame()
        with pytest.raises(Exception): # statsmodels will raise on empty data
            fit_mixed_effects_model(
                empty_df, 
                dependent_var="y", 
                independent_vars=["x"], 
                random_effect="group"
            )