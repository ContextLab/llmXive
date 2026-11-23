"""
Integration test for permutation testing (T030).

This test verifies that the permutation testing logic in
`code/analysis/permutation_test.py` correctly identifies significant
associations between neural activation and computational parameters
when applied to data with a known ground truth correlation.

It uses synthetic data generated from a *different* generative process
than the one used in the main modeling pipeline to ensure robustness.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pytest

# Add code directory to path to allow imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.permutation_test import (
    run_permutation_test,
    fdr_correction,
    generate_null_distribution
)
from utils.config import set_seed
from utils.io import save_json, load_json


def _generate_test_data(n_subjects: int, n_rois: int, correlation_strength: float, seed: int):
    """
    Generate synthetic data with a known correlation structure.

    Args:
        n_subjects: Number of subjects
        n_rois: Number of ROIs
        correlation_strength: The true correlation to embed (e.g., 0.6)
        seed: Random seed for reproducibility

    Returns:
      alpha_params: Array of shape (n_subjects,)
      bold_signals: Array of shape (n_subjects, n_rois)
      expected_significant_indices: List of ROI indices that should be significant
    """
    rng = np.random.default_rng(seed)

    # Generate alpha parameters (behavioral)
    alpha_params = rng.normal(0, 1, n_subjects)

    # Initialize bold signals
    bold_signals = np.zeros((n_subjects, n_rois))

    # Define which ROIs should have a real correlation (e.g., first 3)
    true_correlated_rois = [0, 1, 2]
    expected_significant_indices = true_correlated_rois

    for i in range(n_rois):
        if i in true_correlated_rois:
            # Add correlation: y = x * r + noise
            noise = rng.normal(0, np.sqrt(1 - correlation_strength**2), n_subjects)
            bold_signals[:, i] = alpha_params * correlation_strength + noise
        else:
            # No correlation: pure noise
            bold_signals[:, i] = rng.normal(0, 1, n_subjects)

    return alpha_params, bold_signals, expected_significant_indices


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)


def test_permutation_test_integration(temp_output_dir):
    """
    Integration test: Verify that permutation testing correctly identifies
    significant correlations in synthetic data with known ground truth.

    Steps:
    1. Generate synthetic data with a known correlation (r=0.6) for specific ROIs.
    2. Run the permutation test.
    3. Apply FDR correction.
    4. Verify that the ROIs with ground truth correlation are identified as significant.
    5. Verify that the output file is generated correctly.
    """
    set_seed(42)

    n_subjects = 100
    n_rois = 10
    correlation_strength = 0.6
    n_permutations = 1000
    fdr_threshold = 0.05

    # 1. Generate test data
    alpha_params, bold_signals, expected_significant_indices = _generate_test_data(
        n_subjects, n_rois, correlation_strength, seed=12345
    )

    # 2. Run permutation test
    p_values = run_permutation_test(
        alpha_params,
        bold_signals,
        n_permutations=n_permutations,
        seed=42
    )

    # 3. Apply FDR correction
    is_significant, corrected_p_values = fdr_correction(p_values, q=fdr_threshold)

    # 4. Verify results
    # Check that significant ROIs include the expected ones
    # We allow for some statistical variance, but with N=100 and r=0.6,
    # the power should be very high.
    significant_indices = np.where(is_significant)[0]

    # At least 2 out of the 3 expected ROIs should be significant
    # (allowing for some statistical noise, though with r=0.6 and N=100,
    # we expect almost all to be significant)
    hits = sum(1 for idx in expected_significant_indices if idx in significant_indices)
    assert hits >= 2, f"Expected at least 2 of {expected_significant_indices} to be significant, got {hits}"

    # Ensure no false positives in the non-correlated ROIs are too high
    # (With N=100 and FDR=0.05, we expect ~0.5 false positives on average, so 0 or 1 is acceptable)
    false_positives = sum(1 for idx in significant_indices if idx not in expected_significant_indices)
    assert false_positives <= 2, f"Too many false positives: {false_positives}"

    # 5. Verify output file generation
    output_file = Path(temp_output_dir) / "permutation_results.json"

    results = {
        "p_values": p_values.tolist(),
        "corrected_p_values": corrected_p_values.tolist(),
        "is_significant": is_significant.tolist(),
        "significant_indices": significant_indices.tolist(),
        "n_permutations": n_permutations,
        "fdr_threshold": fdr_threshold,
        "n_subjects": n_subjects,
        "n_rois": n_rois
    }

    save_json(output_file, results)

    assert output_file.exists(), f"Output file {output_file} was not created"

    loaded_results = load_json(output_file)
    assert "p_values" in loaded_results
    assert "is_significant" in loaded_results
    assert len(loaded_results["p_values"]) == n_rois
    assert len(loaded_results["is_significant"]) == n_rois

    # 6. Verify that the permutation test logic actually shuffles correctly
    # by checking that the null distribution is centered around 0
    # (This is implicitly tested by the fact that we get valid p-values,
    # but we can add a specific check here if needed)

    # The mean of p-values for non-correlated ROIs should be roughly 0.5
    non_corr_pvals = [p_values[i] for i in range(n_rois) if i not in expected_significant_indices]
    mean_non_corr_pval = np.mean(non_corr_pvals)
    # With N=1000 permutations, we expect the mean to be close to 0.5,
    # but allow some variance. If it's extremely skewed, something is wrong.
    assert 0.2 < mean_non_corr_pval < 0.8, f"Non-correlated p-values seem biased: mean={mean_non_corr_pval}"


def test_permutation_test_edge_cases(temp_output_dir):
    """
    Test edge cases:
    1. Zero correlation (should yield no significant results after FDR)
    2. Perfect correlation (should yield all significant)
    """
    set_seed(42)

    n_subjects = 50
    n_rois = 5
    n_permutations = 200  # Reduced for speed in edge case test

    # Case 1: Zero correlation
    alpha_params = np.random.default_rng(111).normal(0, 1, n_subjects)
    bold_signals = np.random.default_rng(222).normal(0, 1, (n_subjects, n_rois))

    p_values_zero = run_permutation_test(alpha_params, bold_signals, n_permutations, seed=42)
    is_sig_zero, _ = fdr_correction(p_values_zero, q=0.05)
    # With zero correlation, we expect very few or no significant results
    # (allowing for 1 false positive at 5% FDR)
    assert np.sum(is_sig_zero) <= 1, "Zero correlation test failed: too many significant results"

    # Case 2: Perfect correlation
    alpha_params = np.random.default_rng(333).normal(0, 1, n_subjects)
    bold_signals_perfect = alpha_params.reshape(-1, 1).repeat(n_rois, axis=1) + np.random.default_rng(444).normal(0, 1e-6, (n_subjects, n_rois))

    p_values_perfect = run_permutation_test(alpha_params, bold_signals_perfect, n_permutations, seed=42)
    is_sig_perfect, _ = fdr_correction(p_values_perfect, q=0.05)
    # With perfect correlation, all should be significant
    assert np.sum(is_sig_perfect) == n_rois, "Perfect correlation test failed: not all significant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])