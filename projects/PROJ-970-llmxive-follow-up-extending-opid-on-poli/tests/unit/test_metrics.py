import pytest
import os
import tempfile
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
    def test_exact_match(self):
        trajectory = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 3, 4, 5]
        result = calculate_success_rate(trajectory, ground_truth)
        assert result.success_count == 1
        assert result.rate == 1.0

    def test_subsequence_match(self):
        trajectory = [1, 0, 2, 0, 3, 4, 5]
        ground_truth = [1, 2, 3, 4, 5]
        result = calculate_success_rate(trajectory, ground_truth)
        assert result.success_count == 1
        assert result.rate == 1.0

    def test_no_match(self):
        trajectory = [1, 2, 3]
        ground_truth = [4, 5, 6]
        result = calculate_success_rate(trajectory, ground_truth)
        assert result.success_count == 0
        assert result.rate == 0.0

    def test_empty_ground_truth(self):
        trajectory = [1, 2, 3]
        ground_truth = []
        result = calculate_success_rate(trajectory, ground_truth)
        assert result.success_count == 0
        assert result.rate == 0.0

    def test_trajectory_too_short(self):
        trajectory = [1, 2]
        ground_truth = [1, 2, 3, 4]
        result = calculate_success_rate(trajectory, ground_truth)
        assert result.success_count == 0
        assert result.rate == 0.0

class TestCalculateActionEntropy:
    def test_uniform_distribution(self):
        # Two actions, equal frequency -> entropy = 1.0
        actions = [0, 0, 1, 1]
        entropy = calculate_action_entropy(actions)
        assert abs(entropy - 1.0) < 1e-6

    def test_deterministic(self):
        # All same action -> entropy = 0.0
        actions = [0, 0, 0, 0]
        entropy = calculate_action_entropy(actions)
        assert entropy == 0.0

    def test_empty_actions(self):
        actions = []
        entropy = calculate_action_entropy(actions)
        assert entropy == 0.0

    def test_three_actions_equal(self):
        # Three actions, equal frequency -> entropy = log2(3)
        actions = [0, 1, 2, 0, 1, 2]
        entropy = calculate_action_entropy(actions)
        expected = math.log2(3)
        assert abs(entropy - expected) < 1e-6

class TestCalculateChecksum:
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            calculate_checksum("/nonexistent/path/file.txt")

    def test_binary_content(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"\x00\x01\x02\xff\xfe")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            assert len(checksum) == 64
        finally:
            os.unlink(temp_path)

class TestCalculateRawEntropy:
    def test_uniform_probs(self):
        # [0.25, 0.25, 0.25, 0.25] -> entropy = 2.0
        values = [0.25, 0.25, 0.25, 0.25]
        entropy = calculate_raw_entropy(values)
        assert abs(entropy - 2.0) < 1e-6

    def test_deterministic_prob(self):
        values = [1.0, 0.0, 0.0]
        entropy = calculate_raw_entropy(values)
        assert entropy == 0.0

    def test_empty(self):
        assert calculate_raw_entropy([]) == 0.0

class TestCalculateVariance:
    def test_zero_variance(self):
        values = [5.0, 5.0, 5.0]
        assert calculate_variance(values) == 0.0

    def test_simple_variance(self):
        values = [1.0, 2.0, 3.0]
        # Mean = 2, Var = ((1-2)^2 + (2-2)^2 + (3-2)^2)/3 = 2/3
        expected = 2.0 / 3.0
        assert abs(calculate_variance(values) - expected) < 1e-6

    def test_single_value(self):
        assert calculate_variance([5.0]) == 0.0

class TestCalculateDistillationCostBenefitRatio:
    def test_normal_case(self):
        ratio = calculate_distillation_cost_benefit_ratio(
            mean_log_prob_shift=0.5,
            success_rate_held_out=0.8,
            baseline_success_rate=0.5
        )
        assert ratio == 0.5 / 0.3

    def test_zero_denominator(self):
        ratio = calculate_distillation_cost_benefit_ratio(
            mean_log_prob_shift=0.5,
            success_rate_held_out=0.5,
            baseline_success_rate=0.5
        )
        assert ratio == float('inf')

    def test_negative_denominator(self):
        ratio = calculate_distillation_cost_benefit_ratio(
            mean_log_prob_shift=0.5,
            success_rate_held_out=0.4,
            baseline_success_rate=0.5
        )
        assert ratio == float('inf')