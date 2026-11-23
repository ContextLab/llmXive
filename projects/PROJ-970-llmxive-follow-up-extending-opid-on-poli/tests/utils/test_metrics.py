"""
Unit tests for the metrics calculation utilities.
"""
import pytest
import os
import tempfile
import math
from unittest.mock import patch
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
        """Test when trajectory exactly matches ground truth."""
        trajectory = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 3, 4, 5]
        assert calculate_success_rate(trajectory, ground_truth) == 1.0
    
    def test_no_match(self):
        """Test when trajectory doesn't match ground truth at all."""
        trajectory = [1, 3, 5, 7, 9]
        ground_truth = [2, 4, 6, 8, 10]
        assert calculate_success_rate(trajectory, ground_truth) == 0.0
    
    def test_partial_match(self):
        """Test when trajectory partially matches ground truth."""
        trajectory = [1, 2, 3, 10, 11]
        ground_truth = [1, 2, 3, 4, 5]
        # Should match 3 out of 5 nodes in correct order
        assert calculate_success_rate(trajectory, ground_truth) == 0.6
    
    def test_empty_trajectory(self):
        """Test with empty trajectory."""
        ground_truth = [1, 2, 3]
        assert calculate_success_rate([], ground_truth) == 0.0
    
    def test_empty_ground_truth(self):
        """Test with empty ground truth."""
        trajectory = [1, 2, 3]
        assert calculate_success_rate(trajectory, []) == 0.0
    
    def test_both_empty(self):
        """Test with both empty."""
        assert calculate_success_rate([], []) == 0.0
    
    def test_single_element_match(self):
        """Test with single element match."""
        trajectory = [1]
        ground_truth = [1]
        assert calculate_success_rate(trajectory, ground_truth) == 1.0
    
    def test_single_element_no_match(self):
        """Test with single element no match."""
        trajectory = [1]
        ground_truth = [2]
        assert calculate_success_rate(trajectory, ground_truth) == 0.0


class TestCalculateActionEntropy:
    """Tests for calculate_action_entropy function."""
    
    def test_uniform_distribution(self):
        """Test with uniform action distribution (maximum entropy)."""
        actions = [0, 1, 2, 3]  # 4 unique actions, 1 each
        entropy = calculate_action_entropy(actions)
        # Entropy should be log2(4) = 2.0
        assert math.isclose(entropy, 2.0, rel_tol=1e-9)
    
    def test_deterministic_action(self):
        """Test with deterministic action (zero entropy)."""
        actions = [1, 1, 1, 1, 1]
        assert calculate_action_entropy(actions) == 0.0
    
    def test_empty_actions(self):
        """Test with empty actions list."""
        assert calculate_action_entropy([]) == 0.0
    
    def test_two_actions_equal(self):
        """Test with two actions, equal distribution."""
        actions = [0, 0, 1, 1]  # 2 of each
        entropy = calculate_action_entropy(actions)
        # Entropy should be log2(2) = 1.0
        assert math.isclose(entropy, 1.0, rel_tol=1e-9)
    
    def test_skewed_distribution(self):
        """Test with skewed distribution."""
        actions = [0, 0, 0, 0, 1]  # 4 of 0, 1 of 1
        entropy = calculate_action_entropy(actions)
        # p(0) = 0.8, p(1) = 0.2
        # H = -(0.8 * log2(0.8) + 0.2 * log2(0.2))
        expected = -(0.8 * math.log2(0.8) + 0.2 * math.log2(0.2))
        assert math.isclose(entropy, expected, rel_tol=1e-9)


class TestCalculateChecksum:
    """Tests for calculate_checksum function."""
    
    def test_valid_file(self):
        """Test checksum calculation on a valid file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = calculate_checksum(temp_path)
            # SHA-256 of "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert checksum == expected
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """Test checksum calculation on non-existent file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum("/nonexistent/file/path.txt")
    
    def test_empty_file(self):
        """Test checksum calculation on empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            checksum = calculate_checksum(temp_path)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(temp_path)
    
    def test_binary_file(self):
        """Test checksum calculation on binary file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\x00\x01\x02\x03\x04")
            temp_path = f.name
        
        try:
            checksum = calculate_checksum(temp_path)
            # SHA-256 of bytes
            expected = "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"
            assert checksum == expected
        finally:
            os.unlink(temp_path)


class TestCalculateRawEntropy:
    """Tests for calculate_raw_entropy function."""
    
    def test_uniform_distribution(self):
        """Test with uniform distribution."""
        values = [1, 1, 1, 1]
        entropy = calculate_raw_entropy(values)
        assert math.isclose(entropy, 2.0, rel_tol=1e-9)
    
    def test_empty_values(self):
        """Test with empty values."""
        assert calculate_raw_entropy([]) == 0.0
    
    def test_zero_values(self):
        """Test with all zero values."""
        assert calculate_raw_entropy([0, 0, 0]) == 0.0


class TestCalculateMeanEntropy:
    """Tests for calculate_mean_entropy function."""
    
    def test_mean_of_entropies(self):
        """Test mean calculation of entropy values."""
        entropy_values = [1.0, 2.0, 3.0]
        assert calculate_mean_entropy(entropy_values) == 2.0
    
    def test_empty_list(self):
        """Test with empty list."""
        assert calculate_mean_entropy([]) == 0.0


class TestCalculateVariance:
    """Tests for calculate_variance function."""
    
    def test_variance(self):
        """Test variance calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        # Mean = 3.0
        # Variance = ((1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2) / 5
        #          = (4 + 1 + 0 + 1 + 4) / 5 = 10/5 = 2.0
        assert calculate_variance(values) == 2.0
    
    def test_single_value(self):
        """Test variance with single value."""
        assert calculate_variance([5.0]) == 0.0
    
    def test_empty_list(self):
        """Test variance with empty list."""
        assert calculate_variance([]) == 0.0
    
    def test_identical_values(self):
        """Test variance with identical values."""
        assert calculate_variance([3.0, 3.0, 3.0]) == 0.0


class TestCalculateMeanLogProbShift:
    """Tests for calculate_mean_log_prob_shift function."""
    
    def test_mean_calculation(self):
        """Test mean calculation of log-prob shifts."""
        shifts = [0.1, 0.2, 0.3, 0.4]
        assert calculate_mean_log_prob_shift(shifts) == 0.25
    
    def test_empty_list(self):
        """Test with empty list."""
        assert calculate_mean_log_prob_shift([]) == 0.0


class TestCalculateDistillationCostBenefitRatio:
    """Tests for calculate_distillation_cost_benefit_ratio function."""
    
    def test_normal_case(self):
        """Test normal cost-benefit calculation."""
        mean_shift = 0.5
        improvement = 0.25
        ratio = calculate_distillation_cost_benefit_ratio(mean_shift, improvement)
        assert ratio == 2.0
    
    def test_zero_improvement(self):
        """Test with zero improvement (should return infinity)."""
        mean_shift = 0.5
        improvement = 0.0
        ratio = calculate_distillation_cost_benefit_ratio(mean_shift, improvement)
        assert ratio == float('inf')
    
    def test_negative_improvement(self):
        """Test with negative improvement (should return infinity)."""
        mean_shift = 0.5
        improvement = -0.1
        ratio = calculate_distillation_cost_benefit_ratio(mean_shift, improvement)
        assert ratio == float('inf')
    
    def test_small_improvement(self):
        """Test with very small improvement."""
        mean_shift = 0.1
        improvement = 0.001
        ratio = calculate_distillation_cost_benefit_ratio(mean_shift, improvement)
        assert ratio == 100.0