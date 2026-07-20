import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_path, get_analysis_config, set_seed
from code.analysis import run_sensitivity_analysis, run_analysis_pipeline
from code.synthetic_data import run_synthetic_pipeline

# Fixtures
@pytest.fixture(scope="module")
def synthetic_dataset():
    """
    Generates a synthetic dataset to be used for testing the sensitivity analysis loop.
    This ensures we have valid input data conforming to the project schema.
    """
    set_seed(42)
    # Run the synthetic pipeline to generate data and write to disk
    # This satisfies the requirement that scripts produce real output files
    run_synthetic_pipeline()
    return True

@pytest.fixture(scope="module")
def processed_metrics(synthetic_dataset):
    """
    Ensures the morphological metrics CSV exists from T018.
    """
    metrics_path = get_path("data/processed/morphological_metrics.csv")
    if not os.path.exists(metrics_path):
        # If for some reason T018 wasn't run, run it via the synthetic pipeline
        # The synthetic pipeline should handle the full flow up to T018
        run_synthetic_pipeline()
    return metrics_path

class TestSensitivityAnalysis:
    """
    Unit test for sensitivity analysis loop across Sholl steps {2, 5, 10}.
    This test verifies that the sensitivity analysis function correctly iterates
    through different Sholl radius steps, runs the regression pipeline for each,
    and records the variation in interaction effect p-values.
    """

    def test_sensitivity_analysis_loop_executes(self, processed_metrics):
        """
        Test that run_sensitivity_analysis executes the loop for steps {2, 5, 10}.
        """
        # Ensure the input file exists
        assert os.path.exists(processed_metrics), "Processed metrics file not found"

        # Mock the analysis pipeline to avoid heavy computation but verify loop execution
        # We want to verify the *loop* logic in run_sensitivity_analysis,
        # so we patch the inner heavy-lifting functions to return deterministic values.
        
        mock_results = {
            "step_2": {"interaction_p": 0.045},
            "step_5": {"interaction_p": 0.048},
            "step_10": {"interaction_p": 0.052}
        }

        with patch('code.analysis.run_analysis_pipeline') as mock_pipeline:
            # Configure the mock to return different results based on the step
            # The actual implementation of run_sensitivity_analysis passes step_size as an argument
            # We need to capture the call_args to verify the steps
            call_log = []
            
            def side_effect(*args, **kwargs):
                step = kwargs.get('sholl_step_size', 5) # Default fallback
                call_log.append(step)
                # Return a mock result structure that the sensitivity function expects
                return {
                    "coefficients": {"interaction": 0.5},
                    "p_values": {"interaction": 0.04 + (step * 0.001)},
                    "r2": 0.3
                }
            
            mock_pipeline.side_effect = side_effect

            # Run the sensitivity analysis
            results = run_sensitivity_analysis(
                input_path=processed_metrics,
                steps=[2, 5, 10],
                output_path=str(get_path("data/intermediates/sensitivity_analysis.json"))
            )

            # Verify that the loop ran for all expected steps
            assert len(call_log) == 3, f"Expected 3 iterations, got {len(call_log)}: {call_log}"
            assert 2 in call_log, "Step 2 was not executed"
            assert 5 in call_log, "Step 5 was not executed"
            assert 10 in call_log, "Step 10 was not executed"

            # Verify the output file was created
            output_path = get_path("data/intermediates/sensitivity_analysis.json")
            assert os.path.exists(output_path), "Sensitivity analysis output file not created"

            # Verify the content of the output file
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            
            assert "sensitivity_metrics" in saved_results, "Missing 'sensitivity_metrics' key in output"
            assert "p_value_variations" in saved_results["sensitivity_metrics"], "Missing 'p_value_variations'"
            assert "steps_tested" in saved_results["sensitivity_metrics"], "Missing 'steps_tested'"
            
            # Verify the steps recorded match what we tested
            assert set(saved_results["sensitivity_metrics"]["steps_tested"]) == {2, 5, 10}

    def test_p_value_deviation_calculation(self, processed_metrics):
        """
        Test that the p-value deviation is calculated correctly against a baseline.
        """
        # We use a mock to control the exact p-values returned by the pipeline
        # to ensure the deviation calculation logic is tested deterministically.
        
        # Baseline (step 5) p-value: 0.050
        # Step 2 p-value: 0.040 (20% deviation)
        # Step 10 p-value: 0.060 (20% deviation)
        
        def mock_pipeline_side_effect(*args, **kwargs):
            step = kwargs.get('sholl_step_size', 5)
            if step == 5:
                p_val = 0.050
            elif step == 2:
                p_val = 0.040
            elif step == 10:
                p_val = 0.060
            else:
                p_val = 0.050
            
            return {
                "coefficients": {"interaction": 0.1},
                "p_values": {"interaction": p_val},
                "r2": 0.2
            }

        with patch('code.analysis.run_analysis_pipeline', side_effect=mock_pipeline_side_effect):
            output_path = str(get_path("data/intermediates/sensitivity_analysis_test_deviation.json"))
            results = run_sensitivity_analysis(
                input_path=processed_metrics,
                steps=[2, 5, 10],
                output_path=output_path,
                reference_step=5
            )

            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            p_vars = data["sensitivity_metrics"]["p_value_variations"]
            
            # Check step 2 deviation: abs(0.04 - 0.05) / 0.05 = 0.2
            assert abs(p_vars[2] - 0.2) < 1e-6, f"Step 2 deviation incorrect: {p_vars[2]}"
            # Check step 10 deviation: abs(0.06 - 0.05) / 0.05 = 0.2
            assert abs(p_vars[10] - 0.2) < 1e-6, f"Step 10 deviation incorrect: {p_vars[10]}"

    def test_large_deviation_flagging(self, processed_metrics):
        """
        Test that large deviations are flagged in the output.
        """
        # Step 2: 0.01 (95% deviation from 0.5)
        # Step 5: 0.5 (baseline)
        # Step 10: 0.99 (98% deviation from 0.5)
        
        def mock_pipeline_side_effect(*args, **kwargs):
            step = kwargs.get('sholl_step_size', 5)
            if step == 5:
                p_val = 0.50
            elif step == 2:
                p_val = 0.01
            elif step == 10:
                p_val = 0.99
            else:
                p_val = 0.50
            
            return {
                "coefficients": {"interaction": 0.1},
                "p_values": {"interaction": p_val},
                "r2": 0.2
            }

        with patch('code.analysis.run_analysis_pipeline', side_effect=mock_pipeline_side_effect):
            output_path = str(get_path("data/intermediates/sensitivity_analysis_test_flag.json"))
            results = run_sensitivity_analysis(
                input_path=processed_metrics,
                steps=[2, 5, 10],
                output_path=output_path,
                reference_step=5,
                deviation_threshold=0.5 # Flag if deviation > 50%
            )

            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["sensitivity_metrics"]["max_deviation"] > 0.5
            assert data["sensitivity_metrics"]["flagged"] is True