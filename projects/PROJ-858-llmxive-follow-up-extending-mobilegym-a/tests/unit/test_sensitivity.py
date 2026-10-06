import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sensitivity import (
    calculate_vector_scalar,
    compute_pearson_correlation,
    analyze_sensitivity,
    align_data
)

class TestCalculateVectorScalar:
    def test_sum_ones(self):
        """Test that scalar is the sum of 1s."""
        vector = [1, 0, 1, 1, 0]
        assert calculate_vector_scalar(vector) == 3.0

    def test_all_zeros(self):
        """Test with all zeros."""
        vector = [0, 0, 0]
        assert calculate_vector_scalar(vector) == 0.0

    def test_all_ones(self):
        """Test with all ones."""
        vector = [1, 1, 1, 1]
        assert calculate_vector_scalar(vector) == 4.0

    def test_invalid_input(self):
        """Test that invalid input raises error."""
        with pytest.raises(ValueError):
            calculate_vector_scalar([1, 2, 3])  # 2 is not 0 or 1
        with pytest.raises(ValueError):
            calculate_vector_scalar([1, 0.5, 0])  # 0.5 is not 0 or 1

class TestComputePearsonCorrelation:
    def test_perfect_positive(self):
        """Test perfect positive correlation."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = compute_pearson_correlation(x, y)
        assert abs(r - 1.0) < 1e-6

    def test_perfect_negative(self):
        """Test perfect negative correlation."""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        r = compute_pearson_correlation(x, y)
        assert abs(r - (-1.0)) < 1e-6

    def test_no_correlation(self):
        """Test no correlation (random data)."""
        # Using fixed seed for reproducibility
        np.random.seed(42)
        x = np.random.rand(100)
        y = np.random.rand(100)
        r = compute_pearson_correlation(x.tolist(), y.tolist())
        # Should be close to 0, but not exactly 0
        assert abs(r) < 0.2

    def test_insufficient_data(self):
        """Test that less than 2 points raises error."""
        with pytest.raises(ValueError):
            compute_pearson_correlation([1], [2])
        with pytest.raises(ValueError):
            compute_pearson_correlation([], [])

class TestAnalyzeSensitivity:
    def test_invalid_proxy_flag(self):
        """Test T040: Flag 'Invalid Proxy' if r < 0.3."""
        # Simulate low correlation
        config = {
            "sensitivity": {
                "invalid_threshold": 0.3,
                "validated_threshold": 0.5
            }
        }
        scalars = [1, 2, 3, 4, 5]
        rates = [5, 1, 4, 2, 3]  # Low correlation
        
        results = analyze_sensitivity(config, scalars, rates)
        
        assert results["status"] == "Invalid Proxy"
        assert "Invalid Proxy" in results["recommendation"]
        assert "expand" in results["recommendation"].lower()

    def test_proxy_validated_flag(self):
        """Test T041: Flag 'Proxy Validated' if r >= 0.5."""
        # Simulate high correlation
        config = {
            "sensitivity": {
                "invalid_threshold": 0.3,
                "validated_threshold": 0.5
            }
        }
        scalars = [1, 2, 3, 4, 5]
        rates = [1, 2, 3, 4, 5]  # Perfect correlation
        
        results = analyze_sensitivity(config, scalars, rates)
        
        assert results["status"] == "Proxy Validated"
        assert "Proxy Validated" in results["recommendation"]

    def test_weak_proxy(self):
        """Test intermediate case: 0.3 <= r < 0.5."""
        # Simulate moderate correlation (r ~ 0.4)
        config = {
            "sensitivity": {
                "invalid_threshold": 0.3,
                "validated_threshold": 0.5
            }
        }
        # Create data with moderate correlation
        scalars = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        rates = [1.1, 2.0, 2.8, 4.2, 4.9, 6.1, 6.8, 8.2, 8.9, 10.1]
        
        results = analyze_sensitivity(config, scalars, rates)
        
        assert results["status"] == "Weak Proxy"
        assert "weak" in results["recommendation"].lower()

class TestAlignData:
    def test_align_success(self):
        """Test successful alignment of data."""
        coverage_vectors = [
            {"run_id": "run1", "vector": [1, 0, 1]},
            {"run_id": "run2", "vector": [0, 1, 1]}
        ]
        validation_results = [
            {"run_id": "run1", "success_rate": 0.8},
            {"run_id": "run2", "success_rate": 0.6}
        ]
        
        scalars, rates = align_data(coverage_vectors, validation_results)
        
        assert len(scalars) == 2
        assert len(rates) == 2
        assert scalars[0] == 2.0  # sum([1, 0, 1])
        assert scalars[1] == 2.0  # sum([0, 1, 1])
        assert rates[0] == 0.8
        assert rates[1] == 0.6

    def test_missing_run_id(self):
        """Test handling of missing run_id in validation results."""
        coverage_vectors = [
            {"run_id": "run1", "vector": [1, 0, 1]},
            {"run_id": "run2", "vector": [0, 1, 1]}
        ]
        validation_results = [
            {"run_id": "run1", "success_rate": 0.8}
            # run2 is missing
        ]
        
        scalars, rates = align_data(coverage_vectors, validation_results)
        
        assert len(scalars) == 1
        assert len(rates) == 1
        assert scalars[0] == 2.0
        assert rates[0] == 0.8
