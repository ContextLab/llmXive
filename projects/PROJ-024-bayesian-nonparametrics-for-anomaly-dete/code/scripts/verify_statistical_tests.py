"""
Verification script for statistical tests module.
Tests paired t-test with Bonferroni correction across synthetic dataset scores.
"""

import sys
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.statistical_tests import (
    StatisticalTestResult,
    ComparisonSummary,
    paired_ttest_with_bonferroni,
    compare_all_models,
    format_comparison_summary,
    save_comparison_results
)


def test_paired_ttest_basic():
    """Test basic paired t-test functionality."""
    print("Testing paired t-test with Bonferroni correction...")

    model_a = {"dataset1": 0.85, "dataset2": 0.78, "dataset3": 0.92, "dataset4": 0.81}
    model_b = {"dataset1": 0.72, "dataset2": 0.68, "dataset3": 0.88, "dataset4": 0.75}

    result = paired_ttest_with_bonferroni(
        model_a_scores=model_a,
        model_b_scores=model_b,
        metric="f1_score",
        alpha=0.05,
        bonferroni_factor=3  # 3 pairwise comparisons
    )

    assert isinstance(result, StatisticalTestResult)
    assert result.n_datasets == 4
    assert result.t_statistic != 0.0
    assert 0.0 <= result.p_value <= 1.0
    assert 0.0 <= result.p_value_adjusted <= 1.0
    assert result.mean_diff > 0  # Model A should have higher scores

    print(f"  ✓ Paired t-test passed: t={result.t_statistic:.3f}, p_adj={result.p_value_adjusted:.4f}")
    return True


def test_compare_all_models():
    """Test comparing all models pairwise."""
    print("Testing compare_all_models...")

    model_scores = {
        "Model_A": {"dataset1": 0.85, "dataset2": 0.78, "dataset3": 0.92},
        "Model_B": {"dataset1": 0.72, "dataset2": 0.68, "dataset3": 0.88},
        "Model_C": {"dataset1": 0.65, "dataset2": 0.61, "dataset3": 0.82}
    }

    summary = compare_all_models(model_scores, metric="f1_score", alpha=0.05)

    assert isinstance(summary, ComparisonSummary)
    assert summary.n_models == 3
    assert summary.n_datasets == 3
    assert len(summary.comparisons) == 3  # 3 choose 2 = 3 comparisons

    print(f"  ✓ Compare all models passed: {len(summary.comparisons)} comparisons")
    return True


def test_bonferroni_correction():
    """Test that Bonferroni correction is applied correctly."""
    print("Testing Bonferroni correction...")

    model_a = {"d1": 0.9, "d2": 0.85, "d3": 0.88, "d4": 0.91}
    model_b = {"d1": 0.7, "d2": 0.65, "d3": 0.72, "d4": 0.69}

    result = paired_ttest_with_bonferroni(
        model_a_scores=model_a,
        model_b_scores=model_b,
        metric="f1_score",
        alpha=0.05,
        bonferroni_factor=10  # Large correction factor
    )

    # With large correction factor, adjusted p-value should be larger
    assert result.p_value_adjusted >= result.p_value
    assert result.p_value_adjusted <= 1.0

    print(f"  ✓ Bonferroni correction applied: p={result.p_value:.4f} -> p_adj={result.p_value_adjusted:.4f}")
    return True


def test_insufficient_datasets():
    """Test error handling for insufficient datasets."""
    print("Testing error handling...")

    model_a = {"dataset1": 0.85}
    model_b = {"dataset1": 0.72}

    try:
        paired_ttest_with_bonferroni(model_a, model_b)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "at least 2 common datasets" in str(e)
        print(f"  ✓ Error handling passed: {e}")

    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Statistical Tests Module Verification")
    print("=" * 60)
    print()

    tests = [
        test_paired_ttest_basic,
        test_compare_all_models,
        test_bonferroni_correction,
        test_insufficient_datasets
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\nAll verification tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
