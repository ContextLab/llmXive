"""
Integration tests for FDR correction pipeline (T032).

Verifies that the FDR correction:
1. Correctly processes input p-values across categories and ROIs.
2. Applies Benjamini-Hochberg correction properly.
3. Outputs valid JSON with expected schema.
4. Handles edge cases (empty input, all significant, none significant).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.fdr_correction import apply_fdr_to_results, run_fdr_correction_pipeline


class TestFDRCorrection:
    """Test suite for FDR correction functionality."""

    def test_apply_fdr_to_results_basic(self):
        """Test basic FDR correction with known p-values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        alpha = 0.05

        result = apply_fdr_to_results(p_values, alpha)

        assert "corrected_pvalues" in result
        assert "is_significant" in result
        assert "q_thresholds" in result
        assert len(result["corrected_pvalues"]) == len(p_values)
        assert len(result["is_significant"]) == len(p_values)

        # Check that corrected p-values are >= original (monotonicity)
        for i in range(len(p_values)):
            assert result["corrected_pvalues"][i] >= p_values[i]

    def test_apply_fdr_to_results_empty(self):
        """Test FDR correction with empty input."""
        result = apply_fdr_to_results([], alpha=0.05)

        assert result["corrected_pvalues"] == []
        assert result["is_significant"] == []
        assert result["q_thresholds"] == []

    def test_apply_fdr_to_results_all_significant(self):
        """Test FDR correction where all p-values are very small."""
        p_values = [0.001, 0.002, 0.003]
        result = apply_fdr_to_results(p_values, alpha=0.05)

        # All should be significant
        assert all(result["is_significant"])

    def test_apply_fdr_to_results_none_significant(self):
        """Test FDR correction where all p-values are large."""
        p_values = [0.5, 0.6, 0.7]
        result = apply_fdr_to_results(p_values, alpha=0.05)

        # None should be significant
        assert not any(result["is_significant"])

    def test_run_fdr_correction_pipeline_integration(self, tmp_path):
        """Test full pipeline with synthetic input data."""
        # Create temporary input file
        input_data = {
            "results": [
                {"category": "plot", "roi": "hippocampus", "p_value": 0.01, "accuracy": 0.65},
                {"category": "plot", "roi": "mPFC", "p_value": 0.03, "accuracy": 0.62},
                {"category": "character", "roi": "hippocampus", "p_value": 0.04, "accuracy": 0.60},
                {"category": "character", "roi": "mPFC", "p_value": 0.20, "accuracy": 0.55},
                {"category": "theme", "roi": "PCC", "p_value": 0.005, "accuracy": 0.70},
            ]
        }

        input_path = tmp_path / "decoder_metrics.json"
        output_path = tmp_path / "fdr_corrected_metrics.json"

        with open(input_path, 'w') as f:
            json.dump(input_data, f)

        # Run pipeline
        results = run_fdr_correction_pipeline(
            input_path=str(input_path),
            output_path=str(output_path),
            alpha=0.05
        )

        # Verify output file exists
        assert output_path.exists()

        # Verify output schema
        assert "results" in results
        assert "num_tests" in results
        assert "num_significant" in results
        assert results["num_tests"] == 5

        # Verify each result has required fields
        for res in results["results"]:
            assert "category" in res
            assert "roi" in res
            assert "original_pvalue" in res
            assert "corrected_pvalue" in res
            assert "is_significant_after_fdr" in res

        # Verify at least one is significant (the smallest p-value should survive)
        assert results["num_significant"] >= 1

    def test_run_fdr_correction_pipeline_file_output(self, tmp_path):
        """Test that output file is written correctly."""
        input_data = {
            "results": [
                {"category": "plot", "roi": "hippocampus", "p_value": 0.01},
                {"category": "plot", "roi": "mPFC", "p_value": 0.06},
            ]
        }

        input_path = tmp_path / "decoder_metrics.json"
        output_path = tmp_path / "fdr_corrected_metrics.json"

        with open(input_path, 'w') as f:
            json.dump(input_data, f)

        run_fdr_correction_pipeline(
            input_path=str(input_path),
            output_path=str(output_path),
            alpha=0.05
        )

        # Read and verify file contents
        with open(output_path, 'r') as f:
            saved_data = json.load(f)

        assert "results" in saved_data
        assert len(saved_data["results"]) == 2

    def test_fdr_monotonicity(self):
        """Test that FDR correction preserves monotonicity of significance."""
        # Create p-values in increasing order
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]
        result = apply_fdr_to_results(p_values, alpha=0.05)

        # If a p-value is significant, all smaller p-values should also be significant
        significant_indices = [i for i, sig in enumerate(result["is_significant"]) if sig]

        if significant_indices:
            max_sig_index = max(significant_indices)
            for i in range(max_sig_index + 1):
                assert result["is_significant"][i], f"P-value at index {i} should be significant"