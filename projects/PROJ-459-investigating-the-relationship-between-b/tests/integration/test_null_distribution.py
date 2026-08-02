"""
Integration test for null distribution validation (T030).

This test validates the false positive rate of the correlation analysis
by generating a null distribution through permutation testing.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import get_derived_path, ensure_dirs
from code.analysis.stats import compute_spearman_correlations, apply_bh_correction
from code.utils.io import save_json, load_json


class TestNullDistribution:
    """Tests for null distribution validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure output directories exist."""
        ensure_dirs()

    def test_null_distribution_false_positive_rate(self):
        """
        Test that the false positive rate of the correlation analysis
        is <= 0.05 under the null hypothesis.

        This test:
        1. Generates synthetic data where there is NO true relationship
           between network metrics and genre preferences (random noise).
        2. Runs the correlation analysis on this null data.
        3. Performs permutation testing to generate a null distribution.
        4. Verifies that the observed false positive rate is <= 0.05.
        """
        np.random.seed(42)
        
        # Configuration
        n_subjects = 100
        n_metrics = 5
        n_permutations = 1000
        alpha = 0.05
        
        # Generate null data: random metrics and random genre scores
        # with NO true correlation between them
        metrics_data = np.random.randn(n_subjects, n_metrics)
        metric_names = [f"metric_{i}" for i in range(n_metrics)]
        
        genre_scores = np.random.randn(n_subjects)
        genre_names = ["genre_A"]
        
        # Create DataFrames
        metrics_df = pd.DataFrame(metrics_data, columns=metric_names)
        genre_series = pd.Series(genre_scores, name="genre_A")
        
        # Run actual correlation analysis on null data
        results = compute_spearman_correlations(metrics_df, genre_series)
        
        # Count significant results in actual analysis (should be ~0 under null)
        actual_sig_count = results[results['p_adj'] < alpha].shape[0]
        actual_fp_rate = actual_sig_count / len(results)
        
        # Permutation testing to generate null distribution
        # Shuffle genre scores and recompute correlations many times
        permuted_fp_rates = []
        
        for perm_idx in range(n_permutations):
            # Shuffle genre scores (breaks any potential relationship)
            shuffled_genres = genre_series.sample(frac=1, random_state=perm_idx).reset_index(drop=True)
            
            # Compute correlations on permuted data
            perm_results = compute_spearman_correlations(metrics_df, shuffled_genres)
            
            # Count significant results
            perm_sig_count = perm_results[perm_results['p_adj'] < alpha].shape[0]
            perm_fp_rate = perm_sig_count / len(perm_results)
            permuted_fp_rates.append(perm_fp_rate)
        
        # Calculate statistics of the null distribution
        null_fp_rates = np.array(permuted_fp_rates)
        mean_fp_rate = np.mean(null_fp_rates)
        std_fp_rate = np.std(null_fp_rates)
        
        # The observed false positive rate from actual analysis
        # should be consistent with the null distribution
        # Under the null, we expect ~5% false positives (type I error rate)
        
        # Generate and save the validation report
        report = {
            "test_name": "null_distribution_false_positive_rate",
            "n_subjects": n_subjects,
            "n_metrics": n_metrics,
            "n_permutations": n_permutations,
            "alpha": alpha,
            "actual_false_positive_rate": float(actual_fp_rate),
            "null_distribution_mean_fp_rate": float(mean_fp_rate),
            "null_distribution_std_fp_rate": float(std_fp_rate),
            "null_distribution_95_ci_low": float(np.percentile(null_fp_rates, 2.5)),
            "null_distribution_95_ci_high": float(np.percentile(null_fp_rates, 97.5)),
            "permutations_count": n_permutations,
            "passes_validation": bool(actual_fp_rate <= alpha * 1.5),  # Allow some tolerance
            "description": "Validation of false positive rate under null hypothesis"
        }
        
        # Save the report
        report_path = get_derived_path("null_validation_report.json")
        save_json(report, report_path)
        
        # Assertions
        # The actual false positive rate should be reasonably close to alpha (0.05)
        # We use a generous tolerance (1.5x) to account for sampling variability
        assert actual_fp_rate <= alpha * 1.5, (
            f"False positive rate {actual_fp_rate:.4f} exceeds expected "
            f"threshold {alpha * 1.5:.4f}. The correlation method may be "
            f"producing too many false positives."
        )
        
        # The observed rate should fall within the 95% CI of the null distribution
        assert (report["null_distribution_95_ci_low"] <= actual_fp_rate <= 
               report["null_distribution_95_ci_high"]), (
            f"Observed FP rate {actual_fp_rate:.4f} falls outside the 95% CI "
            f"[{report['null_distribution_95_ci_low']:.4f}, "
            f"{report['null_distribution_95_ci_high']:.4f}] of the null distribution."
        )
        
        # Verify the report was saved
        assert Path(report_path).exists(), "Null validation report was not saved."
        
        # Load and verify report content
        loaded_report = load_json(report_path)
        assert "false_positive_rate" in loaded_report or "actual_false_positive_rate" in loaded_report
        assert "permutations_count" in loaded_report
        
        print(f"\nNull Distribution Validation Report:")
        print(f"  Actual FP Rate: {actual_fp_rate:.4f}")
        print(f"  Null Mean FP Rate: {mean_fp_rate:.4f} ± {std_fp_rate:.4f}")
        print(f"  95% CI: [{report['null_distribution_95_ci_low']:.4f}, {report['null_distribution_95_ci_high']:.4f}]")
        print(f"  Permutations: {n_permutations}")
        print(f"  Passes Validation: {report['passes_validation']}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])