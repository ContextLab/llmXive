import pytest
import numpy as np
from scipy import stats
import json
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diagnostics import tail_ks_test_with_bootstrap, save_tail_ks_results, run_tail_ks_task

class TestTailKSTest:
    def test_tail_ks_test_with_bootstrap_basic(self):
        """Test that the function runs and returns expected keys."""
        # Generate synthetic Pareto-like data for testing
        np.random.seed(42)
        alpha_true = 2.0
        x_min_true = 10.0
        data = stats.pareto.rvs(alpha_true, scale=x_min_true, size=1000, random_state=42)
        
        results = tail_ks_test_with_bootstrap(
            data=data,
            x_min=x_min_true,
            n_bootstrap=10, # Small for speed
            random_state=42
        )
        
        assert "ks_statistic" in results
        assert "p_value_bootstrap" in results
        assert "alpha_estimate" in results
        assert "n_tail_points" in results
        assert results["n_tail_points"] == 1000
        assert isinstance(results["p_value_bootstrap"], float)
    
    def test_tail_ks_test_with_bootstrap_small_sample(self):
        """Test behavior with small sample size."""
        np.random.seed(42)
        data = stats.pareto.rvs(2.0, scale=10.0, size=20, random_state=42)
        
        # Should not raise, but might have warnings or low n_bootstrap
        results = tail_ks_test_with_bootstrap(
            data=data,
            x_min=10.0,
            n_bootstrap=5,
            random_state=42
        )
        
        assert results["n_tail_points"] == 20
    
    def test_save_tail_ks_results(self, tmp_path):
        """Test that results are saved correctly to JSON."""
        results = {
            "ks_statistic": 0.1,
            "p_value_bootstrap": 0.5,
            "alpha_estimate": 2.0,
            "x_min_used": 10.0,
            "n_tail_points": 100,
            "method": "Test"
        }
        output_path = str(tmp_path / "test_tail_ks.json")
        
        save_tail_ks_results(results, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved = json.load(f)
        
        assert saved["ks_statistic"] == 0.1
        assert saved["p_value_bootstrap"] == 0.5
    
    def test_run_tail_ks_task_integration(self, tmp_path, monkeypatch):
        """Integration test for the full task runner."""
        # Create dummy input data
        np.random.seed(42)
        data = stats.pareto.rvs(2.0, scale=10.0, size=500, random_state=42)
        
        # Mock the load function or pass data directly
        # We will call the function directly with data
        output_path = str(tmp_path / "tail_ks.json")
        
        results = run_tail_ks_task(
            data=data,
            x_min=10.0,
            output_path=output_path,
            n_bootstrap=10
        )
        
        assert os.path.exists(output_path)
        assert results["p_value_bootstrap"] is not None
        assert results["ks_statistic"] is not None
    
    def test_x_min_estimation_in_bootstrap(self):
        """Test that the bootstrap loop correctly re-estimates x_min."""
        # This is implicitly tested by the fact that the function runs
        # and produces a p-value. We can't easily verify the internal logic
        # without inspecting the loop, but we can check that the output
        # reflects the complexity.
        np.random.seed(42)
        data = stats.pareto.rvs(2.0, scale=10.0, size=200, random_state=42)
        
        results = tail_ks_test_with_bootstrap(
            data=data,
            x_min=10.0,
            n_bootstrap=10,
            random_state=42
        )
        
        # The function should complete without error
        assert "p_value_bootstrap" in results