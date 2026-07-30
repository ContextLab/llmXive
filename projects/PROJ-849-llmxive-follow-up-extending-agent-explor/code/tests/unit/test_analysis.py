"""
Unit tests for analysis service logic.
"""
import pytest
import numpy as np
from scipy.stats import pearsonr
from services.analysis_service import compute_pearson_correlation, validate_sample_size

class TestValidation:
    def test_validate_sample_size_sufficient(self):
        data = [{"id": i} for i in range(35)]
        assert validate_sample_size(data, min_n=30) is True

    def test_validate_sample_size_insufficient(self):
        data = [{"id": i} for i in range(20)]
        assert validate_sample_size(data, min_n=30) is False

class TestCorrelationCalculation:
    def test_compute_pearson_correlation_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        corr, p = compute_pearson_correlation(x, y)
        assert corr < 0
        assert p < 0.05

    def test_compute_pearson_correlation_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        corr, p = compute_pearson_correlation(x, y)
        assert corr > 0.99
        assert p < 0.05

    def test_compute_pearson_correlation_random(self):
        np.random.seed(42)
        x = np.random.rand(50).tolist()
        y = np.random.rand(50).tolist()
        corr, p = compute_pearson_correlation(x, y)
        # Random data should usually have high p-value
        assert p > 0.05 or abs(corr) < 0.5
