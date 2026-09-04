"""
Unit tests for statistical analysis logic (McNemar's test and Wilcoxon signed-rank test).

This module verifies the correctness of statistical computations using mock data
that mimics the expected input format from the metrics pipeline.

Tests are designed to run independently of the actual data generation pipeline.
"""
import pytest
import numpy as np
from scipy import stats
from pathlib import Path
import sys
import json

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "projects" / "PROJ-886-llmxive-follow-up-extending-dreamx-world"))

from code.analysis.stats import (
    run_mcnemar_test,
    run_wilcoxon_test,
    calculate_censoring_rate,
    calculate_sufficiency_ratio
)


class TestMcNemarLogic:
    """Tests for McNemar's test implementation."""

    def test_mcnemar_on_mock_convergence(self):
        """Test McNemar's test with mock binary convergence data."""
        # Mock data: 50 trajectories
        # Format: list of dicts with 'baseline_converged', 'lite_converged'
        mock_data = [
            {"baseline_converged": True, "lite_converged": True},
            {"baseline_converged": True, "lite_converged": False},
            {"baseline_converged": False, "lite_converged": True},
            {"baseline_converged": False, "lite_converged": False},
            {"baseline_converged": True, "lite_converged": True},
            {"baseline_converged": False, "lite_converged": True},
            {"baseline_converged": True, "lite_converged": False},
            {"baseline_converged": False, "lite_converged": False},
        ] * 6 + [{"baseline_converged": True, "lite_converged": False}]  # 49 total
        mock_data.append({"baseline_converged": False, "lite_converged": True})  # 50 total

        # Construct contingency table manually for verification
        # b = baseline=True, lite=False
        # c = baseline=False, lite=True
        b_count = sum(1 for d in mock_data if d["baseline_converged"] and not d["lite_converged"])
        c_count = sum(1 for d in mock_data if not d["baseline_converged"] and d["lite_converged"])

        result = run_mcnemar_test(mock_data)

        assert "statistic" in result
        assert "p_value" in result
        assert "null_hypothesis" in result
        assert "interpretation" in result

        # Verify statistic calculation (McNemar's chi2 = (|b-c|-1)^2 / (b+c))
        expected_stat = ((abs(b_count - c_count) - 1) ** 2) / (b_count + c_count)
        assert np.isclose(result["statistic"], expected_stat, rtol=1e-5)

    def test_mcnemar_edge_case_equal(self):
        """Test McNemar's test when b == c (statistic should be 0)."""
        mock_data = [
            {"baseline_converged": True, "lite_converged": False},
            {"baseline_converged": False, "lite_converged": True},
        ]

        result = run_mcnemar_test(mock_data)
        assert np.isclose(result["statistic"], 0.0)
        assert result["p_value"] == 1.0  # Perfect symmetry -> p=1

    def test_mcnemar_empty_data(self):
        """Test McNemar's test with empty data."""
        with pytest.raises(ValueError, match="No discordant pairs"):
            run_mcnemar_test([])


class TestWilcoxonLogic:
    """Tests for Wilcoxon signed-rank test implementation."""

    def test_wilcoxon_on_mock_mae(self):
        """Test Wilcoxon test with mock MAE position data."""
        # Mock MAE data for converged trajectories only
        # Format: list of dicts with 'mae_position_baseline', 'mae_position_lite'
        mock_data = [
            {"mae_position_baseline": 0.5, "mae_position_lite": 0.4},
            {"mae_position_baseline": 0.6, "mae_position_lite": 0.5},
            {"mae_position_baseline": 0.7, "mae_position_lite": 0.6},
            {"mae_position_baseline": 0.4, "mae_position_lite": 0.3},
            {"mae_position_baseline": 0.8, "mae_position_lite": 0.7},
        ]

        result = run_wilcoxon_test(mock_data, metric="mae_position")

        assert "statistic" in result
        assert "p_value" in result
        assert "null_hypothesis" in result
        assert "filtered_count" in result
        assert result["filtered_count"] == 5

        # Verify against scipy implementation
        baseline_vals = [d["mae_position_baseline"] for d in mock_data]
        lite_vals = [d["mae_position_lite"] for d in mock_data]
        scipy_stat, scipy_p = stats.wilcoxon(baseline_vals, lite_vals)

        assert np.isclose(result["statistic"], scipy_stat)
        assert np.isclose(result["p_value"], scipy_p, rtol=1e-5)

    def test_wilcoxon_with_nulls_filtered(self):
        """Test that Wilcoxon correctly filters out null/None values."""
        mock_data = [
            {"mae_position_baseline": 0.5, "mae_position_lite": 0.4},
            {"mae_position_baseline": None, "mae_position_lite": 0.5},  # Should be filtered
            {"mae_position_baseline": 0.6, "mae_position_lite": None},  # Should be filtered
            {"mae_position_baseline": 0.7, "mae_position_lite": 0.6},
        ]

        result = run_wilcoxon_test(mock_data, metric="mae_position")

        assert result["filtered_count"] == 2
        assert result["original_count"] == 4

    def test_wilcoxon_insufficient_data(self):
        """Test Wilcoxon with too few samples."""
        mock_data = [
            {"mae_position_baseline": 0.5, "mae_position_lite": 0.4},
        ]

        with pytest.raises(ValueError, match="Insufficient samples"):
            run_wilcoxon_test(mock_data, metric="mae_position")


class TestCensoringRate:
    """Tests for censoring rate calculation."""

    def test_censoring_rate_calculation(self):
        """Test censoring rate with known values."""
        mock_data = [
            {"convergence": True},
            {"convergence": False},
            {"convergence": True},
            {"convergence": False},
            {"convergence": False},
        ]

        result = calculate_censoring_rate(mock_data)

        assert "censoring_rate" in result
        assert "total_count" in result
        assert "censored_count" in result

        # 3 out of 5 are censored (False)
        assert result["censoring_rate"] == 0.6
        assert result["censored_count"] == 3
        assert result["total_count"] == 5

    def test_censoring_rate_empty(self):
        """Test censoring rate with empty data."""
        result = calculate_censoring_rate([])
        assert result["censoring_rate"] == 0.0
        assert result["censored_count"] == 0


class TestSufficiencyRatio:
    """Tests for Information-Theoretic Sufficiency Ratio."""

    def test_sufficiency_ratio_calculation(self):
        """Test sufficiency ratio with mock data."""
        mock_data = [
            {"convergence": True, "mae_position": 0.5},
            {"convergence": True, "mae_position": 0.4},
            {"convergence": True, "mae_position": 0.6},
            {"convergence": False, "mae_position": None},
        ]

        result = calculate_sufficiency_ratio(mock_data)

        assert "sufficiency_ratio" in result
        assert "converged_count" in result
        assert "total_count" in result

        # 3 converged out of 4 total
        assert result["sufficiency_ratio"] == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])