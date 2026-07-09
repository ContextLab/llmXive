"""
Integration tests for statistical analysis, specifically focusing on
multiple-comparison corrections as required by User Story 3.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import numpy as np
import pandas as pd

# Ensure the code directory is in the path for imports
# Adjust relative to where this test file will reside in the project structure
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.analyze.stats import apply_bonferroni_correction, run_statistical_analysis


class TestBonferroniCorrection:
    """
    Integration test for multiple-comparison correction.
    Asserts that p-values are adjusted when testing >= 2 benchmarks.
    """

    def test_bonferroni_correction(self):
        """
        Test that p-values are correctly adjusted using Bonferroni correction
        when multiple benchmarks are tested.
        """
        # Simulate results for 3 benchmarks (GSM8K, MMLU-STEM, MATH)
        # with 10 seeds each.
        num_seeds = 10
        num_benchmarks = 3
        benchmarks = ["gsm8k", "mmlu_stem", "math"]

        # Create synthetic but realistic data
        # Condition A: Static QA (baseline)
        # Condition B: Socratic Dialogue (experimental)
        # We simulate a small effect size to ensure p-values are not trivially 0 or 1
        data = []
        for seed in range(num_seeds):
            for bench_idx, bench_name in enumerate(benchmarks):
                # Generate paired data (same seed, different condition)
                # Using a small fixed offset to simulate a difference
                base_score = 0.5 + (bench_idx * 0.05)  # Vary by benchmark
                static_score = base_score + np.random.normal(0, 0.05, 1)
                socratic_score = static_score + 0.02 + np.random.normal(0, 0.05, 1)

                data.append({
                    "seed": seed,
                    "benchmark": bench_name,
                    "condition": "static",
                    "score": float(static_score[0])
                })
                data.append({
                    "seed": seed,
                    "benchmark": bench_name,
                    "condition": "socratic",
                    "score": float(socratic_score[0])
                })

        df = pd.DataFrame(data)

        # Run the statistical analysis which should include Bonferroni correction
        # The function returns a dictionary with results for each benchmark
        results = run_statistical_analysis(df, correction_method="bonferroni")

        # Verify the structure of the results
        assert isinstance(results, dict), "Results should be a dictionary"
        assert "correction_method" in results, "Results must include correction method"
        assert results["correction_method"] == "bonferroni", "Correction method should be bonferroni"
        assert "raw_p_values" in results, "Results must include raw p-values"
        assert "corrected_p_values" in results, "Results must include corrected p-values"
        assert "num_comparisons" in results, "Results must include number of comparisons"

        # Verify the number of comparisons matches the number of benchmarks
        assert results["num_comparisons"] == num_benchmarks, \
            f"Expected {num_benchmarks} comparisons, got {results['num_comparisons']}"

        # Verify that p-values are adjusted
        raw_p_values = results["raw_p_values"]
        corrected_p_values = results["corrected_p_values"]

        assert len(raw_p_values) == num_benchmarks, \
            f"Expected {num_benchmarks} raw p-values, got {len(raw_p_values)}"
        assert len(corrected_p_values) == num_benchmarks, \
            f"Expected {num_benchmarks} corrected p-values, got {len(corrected_p_values)}"

        # Verify that corrected p-values are >= raw p-values (Bonferroni property)
        for i in range(num_benchmarks):
            assert corrected_p_values[i] >= raw_p_values[i], \
                f"Corrected p-value {corrected_p_values[i]} should be >= raw p-value {raw_p_values[i]}"

        # Verify that corrected p-values are capped at 1.0
        for p_val in corrected_p_values:
            assert p_val <= 1.0, f"Corrected p-value {p_val} should be <= 1.0"

        # Verify the correction logic: corrected = min(raw * num_comparisons, 1.0)
        for i in range(num_benchmarks):
            expected_corrected = min(raw_p_values[i] * num_benchmarks, 1.0)
            # Allow for small floating point differences
            assert abs(corrected_p_values[i] - expected_corrected) < 1e-6, \
                f"Bonferroni correction failed for benchmark {benchmarks[i]}: " \
                f"expected {expected_corrected}, got {corrected_p_values[i]}"

        # Verify that the output includes significance flags based on corrected alpha
        assert "significance_flags" in results, "Results must include significance flags"
        assert len(results["significance_flags"]) == num_benchmarks, \
            f"Expected {num_benchmarks} significance flags, got {len(results['significance_flags'])}"

        # Verify that significance flags are boolean
        for flag in results["significance_flags"]:
            assert isinstance(flag, bool), f"Significance flag {flag} should be boolean"

        # Verify that the output includes the adjusted alpha threshold
        assert "adjusted_alpha" in results, "Results must include adjusted alpha"
        expected_adjusted_alpha = 0.05 / num_benchmarks
        assert abs(results["adjusted_alpha"] - expected_adjusted_alpha) < 1e-6, \
            f"Expected adjusted alpha {expected_adjusted_alpha}, got {results['adjusted_alpha']}"

    def test_bonferroni_correction_single_benchmark(self):
        """
        Test that Bonferroni correction is a no-op when only 1 benchmark is tested.
        """
        num_seeds = 10
        benchmarks = ["gsm8k"]

        data = []
        for seed in range(num_seeds):
            base_score = 0.5 + np.random.normal(0, 0.05, 1)
            data.append({
                "seed": seed,
                "benchmark": benchmarks[0],
                "condition": "static",
                "score": float(base_score[0])
            })
            data.append({
                "seed": seed,
                "benchmark": benchmarks[0],
                "condition": "socratic",
                "score": float(base_score[0] + 0.02 + np.random.normal(0, 0.05, 1)[0])
            })

        df = pd.DataFrame(data)
        results = run_statistical_analysis(df, correction_method="bonferroni")

        # With 1 comparison, corrected p-value should equal raw p-value
        assert results["num_comparisons"] == 1
        assert abs(results["corrected_p_values"][0] - results["raw_p_values"][0]) < 1e-6
        assert abs(results["adjusted_alpha"] - 0.05) < 1e-6

    def test_bonferroni_correction_output_file(self):
        """
        Test that the analysis script writes a valid JSON output file
        containing the corrected p-values.
        """
        num_seeds = 10
        benchmarks = ["gsm8k", "mmlu_stem"]

        data = []
        for seed in range(num_seeds):
            for bench_name in benchmarks:
                base_score = 0.5 + np.random.normal(0, 0.05, 1)
                data.append({
                    "seed": seed,
                    "benchmark": bench_name,
                    "condition": "static",
                    "score": float(base_score[0])
                })
                data.append({
                    "seed": seed,
                    "benchmark": bench_name,
                    "condition": "socratic",
                    "score": float(base_score[0] + 0.02 + np.random.normal(0, 0.05, 1)[0])
                })

        df = pd.DataFrame(data)

        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Run analysis and write to file
            results = run_statistical_analysis(df, correction_method="bonferroni")

            # Manually write results to file to simulate script behavior
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

            # Read back and verify
            with open(output_path, 'r') as f:
                loaded_results = json.load(f)

            assert "corrected_p_values" in loaded_results
            assert len(loaded_results["corrected_p_values"]) == 2
            assert all(p <= 1.0 for p in loaded_results["corrected_p_values"])
        finally:
            # Clean up temp file
            if os.path.exists(output_path):
                os.remove(output_path)