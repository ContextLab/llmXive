"""
Integration tests for gradient stability analysis (US1).

This module verifies SC-002 by analyzing gradient norms from baseline training.
It depends on T012b which populates data/logs/gradient_norms.json.
"""
import pytest
import json
import os
from pathlib import Path
import numpy as np
from typing import List, Dict, Any

# Import the utility function from the statistics module
from src.utils.statistics import load_gradient_norms, compare_gradient_stability

# Constants for paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
GRADIENT_LOG_PATH = PROJECT_ROOT / "data" / "logs" / "gradient_norms.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "gradient_stability_baseline.json"

class TestGradientLogging:
    """Tests to ensure gradient logging infrastructure works correctly."""
    
    def test_gradient_log_file_exists(self):
        """Verify that the gradient log file exists after training (T012b)."""
        assert GRADIENT_LOG_PATH.exists(), (
            f"Gradient log file not found at {GRADIENT_LOG_PATH}. "
            "Ensure T012b (baseline training with logging) has been executed."
        )
    
    def test_gradient_log_schema(self):
        """Verify the gradient log file has the expected schema."""
        if not GRADIENT_LOG_PATH.exists():
            pytest.skip("Gradient log file does not exist yet.")
        
        with open(GRADIENT_LOG_PATH, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "Gradient log must be a dictionary."
        assert "steps" in data, "Gradient log must contain a 'steps' key."
        assert isinstance(data["steps"], list), "Steps must be a list."
        
        if len(data["steps"]) > 0:
            step = data["steps"][0]
            assert "step" in step, "Each step entry must have a 'step' index."
            assert "norm" in step, "Each step entry must have a 'norm' value."
            assert isinstance(step["norm"], (int, float)), "Norm must be numeric."

class TestGradientStabilityBaseline:
    """
    Statistical test for gradient stability in the baseline model (US1).
    
    Logic:
    1. Load gradient norms from data/logs/gradient_norms.json.
    2. Compute mean and standard deviation of the norms.
    3. Determine stability: A model is considered 'stable' if the coefficient of
       variation (std/mean) is below a threshold (e.g., 0.5) or if the variance
       is not excessively high relative to the mean.
    4. Output results to data/results/gradient_stability_baseline.json.
    """
    
    def test_baseline_stability_analysis(self, tmp_path):
        """
        Run the stability analysis on baseline gradient norms.
        
        This test performs the actual analysis and writes the result file.
        It serves as the integration test for SC-002 verification for US1.
        """
        if not GRADIENT_LOG_PATH.exists():
            pytest.skip(
                "Gradient log file not found. "
                "Please run T012b (baseline training with logging) first."
            )
        
        # Load gradient norms
        norms = load_gradient_norms(GRADIENT_LOG_PATH)
        
        if len(norms) < 2:
            # Not enough data points for statistical analysis
            result = {
                "mean_norm": float(norms[0]) if norms else 0.0,
                "std_norm": 0.0,
                "is_stable": False,
                "note": "Insufficient data points for stability analysis"
            }
        else:
            norms_array = np.array(norms)
            mean_norm = float(np.mean(norms_array))
            std_norm = float(np.std(norms_array))
            
            # Stability criterion: Coefficient of Variation (CV) < 0.5
            # If mean is 0, we consider it unstable to avoid division by zero
            if mean_norm > 0:
                cv = std_norm / mean_norm
                is_stable = cv < 0.5
            else:
                is_stable = False
            
            result = {
                "mean_norm": round(mean_norm, 6),
                "std_norm": round(std_norm, 6),
                "is_stable": is_stable,
                "coefficient_of_variation": round(cv if mean_norm > 0 else 0.0, 6)
            }
        
        # Write output to the required path
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Verify the output file was created
        assert OUTPUT_PATH.exists(), "Output file was not created."
        
        # Verify the schema of the output
        with open(OUTPUT_PATH, 'r') as f:
            output_data = json.load(f)
        
        assert "mean_norm" in output_data
        assert "std_norm" in output_data
        assert "is_stable" in output_data
        assert isinstance(output_data["mean_norm"], float)
        assert isinstance(output_data["std_norm"], float)
        assert isinstance(output_data["is_stable"], bool)
        
        # Assert that the analysis actually ran (basic sanity check)
        assert result["mean_norm"] >= 0, "Mean norm must be non-negative"
        assert result["std_norm"] >= 0, "Std norm must be non-negative"
    
    def test_stability_result_consistency(self):
        """
        Verify that running the analysis again produces consistent results.
        """
        if not GRADIENT_LOG_PATH.exists():
            pytest.skip("Gradient log file not found.")
        
        # Run analysis logic again
        norms = load_gradient_norms(GRADIENT_LOG_PATH)
        if len(norms) < 2:
            pytest.skip("Insufficient data points for consistency check.")
        
        norms_array = np.array(norms)
        expected_mean = float(np.mean(norms_array))
        expected_std = float(np.std(norms_array))
        
        # Load the previously written result
        if not OUTPUT_PATH.exists():
            pytest.skip("Result file not found. Run test_baseline_stability_analysis first.")
        
        with open(OUTPUT_PATH, 'r') as f:
            result = json.load(f)
        
        # Check consistency (allowing for small floating point differences)
        assert abs(result["mean_norm"] - expected_mean) < 1e-6, "Mean norm mismatch"
        assert abs(result["std_norm"] - expected_std) < 1e-6, "Std norm mismatch"