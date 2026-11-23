"""
Integration test for meta-analysis aggregation (T021).

This test verifies that the meta-analysis pipeline correctly aggregates
effect sizes from multiple datasets into a Random-Effects model,
separating Causal and Associational pools as per User Story 2.

It uses synthetic data generated on-the-fly to simulate the output
of the analysis stage (coefficients, standard errors, study IDs)
and feeds them into the aggregation logic in `code/analysis.py`.

Note: This test does NOT run the full ingestion pipeline (T011-T015)
to avoid network dependencies and time constraints. It mocks the
intermediate analysis results to focus strictly on the meta-analysis
aggregation logic (T028).
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pytest

# Import the analysis module to test the aggregation logic
# We assume `code/analysis.py` contains `run_meta_analysis` or similar
# Since T028 (implementation) is not yet done, we will mock the logic
# or implement a minimal version here if the import fails, but the task
# is to write the TEST. The test should fail if the implementation is missing.
try:
    from analysis import run_meta_analysis
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False

# Mock data generator for analysis results
def generate_mock_analysis_results(
    n_studies: int = 5,
    pool_type: str = "causal"
) -> List[Dict[str, Any]]:
    """
    Generates a list of mock analysis results simulating the output
    of T027 (coefficient extractor).

    Each study result contains:
    - study_id: unique identifier
    - pool: 'causal' or 'associational'
    - zero_inflation_coef: log-odds coefficient
    - zero_inflation_se: standard error
    - positive_coef: log-scale coefficient (for Gamma)
    - positive_se: standard error
    - n_samples: sample size
    """
    np.random.seed(42) # Deterministic for testing
    results = []
    for i in range(n_studies):
        # Simulate some effect sizes
        # Causal pool might have a stronger negative effect for exclusion
        base_effect = -0.5 if pool_type == "causal" else -0.1
        noise = np.random.normal(0, 0.2)

        results.append({
            "study_id": f"study_{i:03d}",
            "pool": pool_type,
            "zero_inflation_coef": base_effect + noise,
            "zero_inflation_se": np.abs(np.random.normal(0.1, 0.02)),
            "positive_coef": base_effect + noise,
            "positive_se": np.abs(np.random.normal(0.1, 0.02)),
            "n_samples": np.random.randint(50, 200)
        })
    return results

class TestMetaAnalysisAggregation:
    """
    Integration tests for the meta-analysis aggregation logic.
    """

    def test_meta_analysis_aggregation_logic(self):
        """
        Test that the meta-analysis function correctly aggregates
        coefficients from multiple studies into a Random-Effects model.

        This test:
        1. Generates mock analysis results for Causal and Associational pools.
        2. Calls the aggregation function.
        3. Verifies the output contains expected keys (combined effect, SE, CI, I^2).
        4. Verifies the result is written to the correct output file path.
        """
        if not HAS_IMPLEMENTATION:
            # If the implementation is not ready, the test should fail loudly
            # to indicate the dependency (T028) is missing.
            pytest.fail(
                "Implementation of meta-analysis aggregation (T028) is missing. "
                "The function `run_meta_analysis` could not be imported from `analysis`."
            )

        # Setup temporary directory for output
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "meta_analysis_results.json"

            # Prepare mock data
            causal_results = generate_mock_analysis_results(n_studies=5, pool_type="causal")
            associational_results = generate_mock_analysis_results(n_studies=3, pool_type="associational")

            # Save mock data to a temporary file (simulating the input from T027)
            mock_input_path = Path(tmp_dir) / "analysis_results.json"
            with open(mock_input_path, 'w') as f:
                json.dump({
                    "causal": causal_results,
                    "associational": associational_results
                }, f)

            # Run the meta-analysis
            # Assuming the function signature: run_meta_analysis(input_path, output_path)
            # If the actual signature differs, this will raise an error, which is the desired behavior
            # to indicate the test needs to be updated or the implementation is wrong.
            try:
                run_meta_analysis(
                    input_path=str(mock_input_path),
                    output_path=str(output_path)
                )
            except Exception as e:
                pytest.fail(f"Meta-analysis execution failed: {e}")

            # Verify output file exists
            assert output_path.exists(), "Meta-analysis output file was not created."

            # Verify content structure
            with open(output_path, 'r') as f:
                result = json.load(f)

            # Check for required keys in the result
            assert "causal_pool" in result, "Causal pool results missing in output."
            assert "associational_pool" in result, "Associational pool results missing in output."

            # Validate Causal Pool structure
            causal_meta = result["causal_pool"]
            assert "combined_effect" in causal_meta, "Combined effect missing for causal pool."
            assert "standard_error" in causal_meta, "Standard error missing for causal pool."
            assert "confidence_interval_95" in causal_meta, "95% CI missing for causal pool."
            assert "heterogeneity_i2" in causal_meta, "Heterogeneity (I^2) missing for causal pool."
            assert "n_studies" in causal_meta, "Number of studies missing for causal pool."

            # Validate Associational Pool structure
            assoc_meta = result["associational_pool"]
            assert "combined_effect" in assoc_meta, "Combined effect missing for associational pool."
            assert "standard_error" in assoc_meta, "Standard error missing for associational pool."
            assert "confidence_interval_95" in assoc_meta, "95% CI missing for associational pool."
            assert "heterogeneity_i2" in assoc_meta, "Heterogeneity (I^2) missing for associational pool."
            assert "n_studies" in assoc_meta, "Number of studies missing for associational pool."

            # Verify numerical plausibility (effect sizes should be floats)
            assert isinstance(causal_meta["combined_effect"], (int, float)), "Combined effect must be numeric."
            assert isinstance(causal_meta["heterogeneity_i2"], (int, float)), "I^2 must be numeric."

            # Verify that the number of studies matches the input
            assert causal_meta["n_studies"] == 5, f"Expected 5 causal studies, got {causal_meta['n_studies']}"
            assert assoc_meta["n_studies"] == 3, f"Expected 3 associational studies, got {assoc_meta['n_studies']}"

    def test_meta_analysis_empty_pool_handling(self):
        """
        Test that the meta-analysis function handles empty pools gracefully.
        """
        if not HAS_IMPLEMENTATION:
            pytest.skip("Implementation not available")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "meta_analysis_empty.json"
            mock_input_path = Path(tmp_dir) / "analysis_results_empty.json"

            # Input with one empty pool
            with open(mock_input_path, 'w') as f:
                json.dump({
                    "causal": [],
                    "associational": generate_mock_analysis_results(n_studies=2, pool_type="associational")
                }, f)

            try:
                run_meta_analysis(
                    input_path=str(mock_input_path),
                    output_path=str(output_path)
                )
            except Exception as e:
                # Depending on implementation, it might raise an error or return nulls
                # For this test, we expect it to handle it without crashing the pipeline
                # If it raises, we check if it's a specific "Insufficient Data" error
                if "Insufficient Data" in str(e) or "No studies" in str(e):
                    pass # Expected behavior
                else:
                    pytest.fail(f"Unexpected error handling empty pool: {e}")

            if output_path.exists():
                with open(output_path, 'r') as f:
                    result = json.load(f)
                
                # Verify the empty pool is represented (e.g., null or specific flag)
                # Implementation details may vary, but the key should exist
                assert "causal_pool" in result, "Causal pool key missing even if empty."
                # If the implementation returns None for empty, check that
                if result["causal_pool"] is None:
                    pass
                else:
                    # Or if it returns a structure with 0 studies
                    assert result["causal_pool"].get("n_studies", 0) == 0

    def test_meta_analysis_reproducibility(self):
        """
        Test that running the meta-analysis twice with the same input
        produces identical output (deterministic).
        """
        if not HAS_IMPLEMENTATION:
            pytest.skip("Implementation not available")

        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_input_path = Path(tmp_dir) / "analysis_results_repro.json"
            output_path_1 = Path(tmp_dir) / "meta_1.json"
            output_path_2 = Path(tmp_dir) / "meta_2.json"

            data = {
                "causal": generate_mock_analysis_results(n_studies=4, pool_type="causal"),
                "associational": generate_mock_analysis_results(n_studies=2, pool_type="associational")
            }
            
            with open(mock_input_path, 'w') as f:
                json.dump(data, f)

            # Run twice
            run_meta_analysis(str(mock_input_path), str(output_path_1))
            run_meta_analysis(str(mock_input_path), str(output_path_2))

            # Compare
            with open(output_path_1, 'r') as f:
                res1 = json.load(f)
            with open(output_path_2, 'r') as f:
                res2 = json.load(f)

            assert res1 == res2, "Meta-analysis results are not deterministic."