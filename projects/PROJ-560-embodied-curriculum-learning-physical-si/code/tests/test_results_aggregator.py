import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.models import AnalysisResult, SensitivitySweep
from src.results_aggregator import aggregate_and_write_results

class TestResultsAggregator:
    
    def test_aggregate_and_write_results_without_sweep(self, tmp_path):
        """Test that results are written correctly without sensitivity sweep data."""
        # Create a mock AnalysisResult
        analysis_result = AnalysisResult(
            t_test={"statistic": 2.5, "pvalue": 0.01, "method": "welch"},
            effect_size={"cohens_d": 0.8, "interpretation": "large"},
            confidence_interval={"lower": 0.2, "upper": 1.4},
            bonferroni_adjusted={"adjusted_alpha": 0.005, "is_significant": True},
            inference_framing="Associational only.",
            collinearity_diagnostics={"max_r": 0.1, "flagged": False},
            power_analysis={"achieved_power": 0.95, "flag": "adequate"},
            metadata={"n_total": 100, "seed": 42},
            sensitivity_sweep=[]
        )

        output_file = tmp_path / "results.json"
        
        result_path = aggregate_and_write_results(
            analysis_result, 
            sweep_results=None, 
            output_path=str(output_file)
        )

        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert "sensitivity_sweep" in data
        assert data["sensitivity_sweep"] == []
        assert data["effect_size"]["cohens_d"] == 0.8

    def test_aggregate_and_write_results_with_sweep(self, tmp_path):
        """Test that sweep results are correctly appended to the main JSON report (T031)."""
        # Create a mock AnalysisResult
        analysis_result = AnalysisResult(
            t_test={"statistic": 2.5, "pvalue": 0.01, "method": "welch"},
            effect_size={"cohens_d": 0.8, "interpretation": "large"},
            confidence_interval={"lower": 0.2, "upper": 1.4},
            bonferroni_adjusted={"adjusted_alpha": 0.005, "is_significant": True},
            inference_framing="Associational only.",
            collinearity_diagnostics={"max_r": 0.1, "flagged": False},
            power_analysis={"achieved_power": 0.95, "flag": "adequate"},
            metadata={"n_total": 100, "seed": 42},
            sensitivity_sweep=[]
        )

        # Create mock SensitivitySweep objects
        sweep1 = SensitivitySweep(
            threshold=0.01,
            effect_size=0.75,
            p_value=0.02,
            sample_size=95,
            robustness_warning=False
        )
        sweep2 = SensitivitySweep(
            threshold=0.05,
            effect_size=0.60,
            p_value=0.04,
            sample_size=90,
            robustness_warning=True
        )

        output_file = tmp_path / "results_with_sweep.json"
        
        result_path = aggregate_and_write_results(
            analysis_result, 
            sweep_results=[sweep1, sweep2], 
            output_path=str(output_file)
        )

        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        # Verify sweep results are present
        assert "sensitivity_sweep" in data
        assert len(data["sensitivity_sweep"]) == 2
        
        # Verify specific fields
        assert data["sensitivity_sweep"][0]["threshold"] == 0.01
        assert data["sensitivity_sweep"][0]["effect_size"] == 0.75
        assert data["sensitivity_sweep"][1]["robustness_warning"] is True

    def test_output_directory_creation(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        analysis_result = AnalysisResult(
            t_test={}, effect_size={}, confidence_interval={},
            bonferroni_adjusted={}, inference_framing="",
            collinearity_diagnostics={}, power_analysis={},
            metadata={}, sensitivity_sweep=[]
        )

        # Path with non-existent subdirectories
        deep_path = tmp_path / "deep" / "nested" / "dir" / "results.json"
        
        result_path = aggregate_and_write_results(
            analysis_result, 
            output_path=str(deep_path)
        )

        assert result_path.exists()
        assert result_path.parent.exists()