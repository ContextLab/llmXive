import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.stats import run_epsilon_sensitivity_analysis

class TestPilotSensitivityAnalysis:
    """Tests for the pilot sensitivity analysis functionality."""
    
    def test_run_epsilon_sensitivity_analysis_basic(self):
        """Test basic execution of pilot sensitivity analysis."""
        epsilon_values = [1e-6, 1e-5, 1e-4]
        results = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=10,
            num_matrices=5,
            seed=42
        )
        
        assert "pilot_config" in results
        assert "results" in results
        assert "summary" in results
        
        assert len(results["results"]) == len(epsilon_values)
        
        for result in results["results"]:
            assert "epsilon" in result
            assert "accumulated_kl_divergence_error_rate" in result
            assert "variation_rate" in result
            assert "num_steps_run" in result
            assert "total_accumulated_kl" in result
    
    def test_epsilon_values_match_input(self):
        """Test that output epsilon values match input values."""
        epsilon_values = [1e-6, 1e-5, 1e-4]
        results = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=10,
            num_matrices=5,
            seed=42
        )
        
        output_epsilons = [r["epsilon"] for r in results["results"]]
        assert output_epsilons == epsilon_values
    
    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with the same seed."""
        epsilon_values = [1e-5]
        
        results1 = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=10,
            num_matrices=5,
            seed=123
        )
        
        results2 = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=10,
            num_matrices=5,
            seed=123
        )
        
        # Results should be identical with same seed
        assert results1["results"][0]["accumulated_kl_divergence_error_rate"] == \
               results2["results"][0]["accumulated_kl_divergence_error_rate"]
    
    def test_summary_contains_best_epsilon(self):
        """Test that summary contains best epsilon selection."""
        epsilon_values = [1e-6, 1e-5, 1e-4]
        results = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=10,
            num_matrices=5,
            seed=42
        )
        
        assert "best_epsilon" in results["summary"]
        assert "min_error_rate" in results["summary"]
        
        # Best epsilon should be one of the tested values
        assert results["summary"]["best_epsilon"] in epsilon_values
    
    def test_error_rate_computation(self):
        """Test that error rate is computed correctly."""
        epsilon_values = [1e-5]
        num_steps = 20
        results = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=num_steps,
            num_matrices=5,
            seed=42
        )
        
        result = results["results"][0]
        # Error rate should be total accumulated KL divided by num_steps
        expected_error_rate = result["total_accumulated_kl"] / num_steps
        assert abs(result["accumulated_kl_divergence_error_rate"] - expected_error_rate) < 1e-10
    
    def test_variation_rate_is_positive(self):
        """Test that variation rate is non-negative."""
        epsilon_values = [1e-5]
        results = run_epsilon_sensitivity_analysis(
            epsilon_values=epsilon_values,
            num_steps=10,
            num_matrices=5,
            seed=42
        )
        
        for result in results["results"]:
            assert result["variation_rate"] >= 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
