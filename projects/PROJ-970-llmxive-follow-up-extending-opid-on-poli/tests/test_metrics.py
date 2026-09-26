"""
Unit tests for the metrics calculation utilities.
"""
import os
import tempfile
import pytest
import numpy as np

from utils.metrics import (
    calculate_success_rate,
    calculate_action_entropy,
    calculate_checksum,
    calculate_raw_entropy,
    calculate_mean_entropy,
    calculate_variance,
    calculate_mean_log_prob_shift,
    calculate_distillation_cost_benefit_ratio,
    SuccessRateResult
)


class TestCalculateSuccessRate:
    """Tests for calculate_success_rate function."""

    def test_exact_match(self):
        """Test that exact match returns True."""
        trajectory = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 3, 4, 5]
        assert calculate_success_rate(trajectory, ground_truth) is True

    def test_mismatch_length(self):
        """Test that different lengths return False."""
        trajectory = [1, 2, 3]
        ground_truth = [1, 2, 3, 4]
        assert calculate_success_rate(trajectory, ground_truth) is False

    def test_mismatch_values(self):
        """Test that different values return False."""
        trajectory = [1, 2, 3, 4]
        ground_truth = [1, 2, 5, 4]
        assert calculate_success_rate(trajectory, ground_truth) is False

    def test_empty_trajectory(self):
        """Test that empty trajectory returns False."""
        assert calculate_success_rate([], [1, 2, 3]) is False

    def test_empty_ground_truth(self):
        """Test that empty ground truth returns False."""
        assert calculate_success_rate([1, 2, 3], []) is False

    def test_both_empty(self):
        """Test that both empty returns False."""
        assert calculate_success_rate([], []) is False


class TestCalculateActionEntropy:
    """Tests for calculate_action_entropy function."""

    def test_uniform_distribution(self):
        """Test entropy calculation for uniform distribution."""
        # 4 actions, each appearing once -> uniform, max entropy
        actions = [0, 1, 2, 3]
        entropy = calculate_action_entropy(actions)
        expected = 2.0  # log2(4)
        assert abs(entropy - expected) < 1e-6

    def test_deterministic_action(self):
        """Test entropy for deterministic (single action) sequence."""
        actions = [0, 0, 0, 0]
        entropy = calculate_action_entropy(actions)
        assert entropy == 0.0

    def test_empty_actions(self):
        """Test entropy for empty action list."""
        entropy = calculate_action_entropy([])
        assert entropy == 0.0

    def test_two_actions_imbalanced(self):
        """Test entropy for imbalanced two-action distribution."""
        actions = [0, 0, 0, 0, 1]  # 80% action 0, 20% action 1
        entropy = calculate_action_entropy(actions)
        # p0=0.8, p1=0.2
        expected = -(0.8 * np.log2(0.8) + 0.2 * np.log2(0.2))
        assert abs(entropy - expected) < 1e-6

    def test_with_explicit_action_space(self):
        """Test entropy with explicit action space size."""
        actions = [0, 1]
        # Without explicit space: max(actions)+1 = 2 -> entropy = 1.0
        # With explicit space = 4: probabilities [0.5, 0.5, 0, 0] -> entropy = 1.0
        entropy = calculate_action_entropy(actions, action_space_size=4)
        assert entropy == 1.0


class TestCalculateChecksum:
    """Tests for calculate_checksum function."""

    def test_known_file(self):
        """Test checksum calculation for a known file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            # SHA256 of "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum("/nonexistent/path/file.txt")

    def test_md5_algorithm(self):
        """Test checksum with MD5 algorithm."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path, algorithm="md5")
            # MD5 of "test"
            expected = "098f6bcd4621d373cade4e832627b4f6"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_invalid_algorithm(self):
        """Test that ValueError is raised for invalid algorithm."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                calculate_checksum(temp_path, algorithm="invalid_algo")
        finally:
            os.unlink(temp_path)


class TestCalculateRawEntropy:
    """Tests for calculate_raw_entropy function."""

    def test_uniform_distribution(self):
        """Test raw entropy for uniform distribution."""
        probs = [0.25, 0.25, 0.25, 0.25]
        entropy = calculate_raw_entropy(probs)
        assert abs(entropy - 2.0) < 1e-6

    def test_deterministic(self):
        """Test raw entropy for deterministic distribution."""
        probs = [1.0, 0.0, 0.0]
        entropy = calculate_raw_entropy(probs)
        assert entropy == 0.0

    def test_empty_list(self):
        """Test raw entropy for empty list."""
        entropy = calculate_raw_entropy([])
        assert entropy == 0.0


class TestCalculateMeanEntropy:
    """Tests for calculate_mean_entropy function."""

    def test_basic_mean(self):
        """Test mean calculation."""
        values = [1.0, 2.0, 3.0]
        assert calculate_mean_entropy(values) == 2.0

    def test_empty_list(self):
        """Test mean for empty list."""
        assert calculate_mean_entropy([]) == 0.0


class TestCalculateVariance:
    """Tests for calculate_variance function."""

    def test_basic_variance(self):
        """Test variance calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        # Population variance: 2.0
        assert abs(calculate_variance(values) - 2.0) < 1e-6

    def test_single_value(self):
        """Test variance for single value (should be 0)."""
        assert calculate_variance([5.0]) == 0.0

    def test_empty_list(self):
        """Test variance for empty list."""
        assert calculate_variance([]) == 0.0


class TestCalculateMeanLogProbShift:
    """Tests for calculate_mean_log_prob_shift function."""

    def test_basic_mean(self):
        """Test mean calculation."""
        shifts = [0.1, 0.2, 0.3]
        assert calculate_mean_log_prob_shift(shifts) == 0.2

    def test_empty_list(self):
        """Test mean for empty list."""
        assert calculate_mean_log_prob_shift([]) == 0.0


class TestCalculateDistillationCostBenefitRatio:
    """Tests for calculate_distillation_cost_benefit_ratio function."""

    def test_basic_ratio(self):
        """Test basic ratio calculation."""
        ratio = calculate_distillation_cost_benefit_ratio(
            mean_log_prob_shift=1.0,
            success_rate_full=0.8,
            baseline_success_rate=0.5
        )
        # 1.0 / (0.8 - 0.5) = 1.0 / 0.3 = 3.333...
        assert abs(ratio - 3.333333) < 1e-4

    def test_zero_denominator(self):
        """Test behavior when denominator is zero."""
        ratio = calculate_distillation_cost_benefit_ratio(
            mean_log_prob_shift=1.0,
            success_rate_full=0.5,
            baseline_success_rate=0.5
        )
        assert ratio == float('inf')

    def test_negative_ratio(self):
        """Test negative ratio calculation."""
        ratio = calculate_distillation_cost_benefit_ratio(
            mean_log_prob_shift=-1.0,
            success_rate_full=0.5,
            baseline_success_rate=0.8
        )
        # -1.0 / (0.5 - 0.8) = -1.0 / -0.3 = 3.333...
        assert abs(ratio - 3.333333) < 1e-4