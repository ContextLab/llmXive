import pytest
import numpy as np
from scipy.stats import pearsonr
from services.analysis_service import compute_pearson_correlation, validate_sample_size

def test_validate_sample_size_sufficient():
    data = [{"id": i} for i in range(30)]
    assert validate_sample_size(data, min_size=30) is True

def test_validate_sample_size_insufficient():
    data = [{"id": i} for i in range(20)]
    assert validate_sample_size(data, min_size=30) is False

def test_compute_pearson_correlation_negative():
    x = [1, 2, 3, 4, 5]
    y = [5, 4, 3, 2, 1]
    corr, p = compute_pearson_correlation(x, y)
    assert corr < 0
    assert p < 0.05

def test_compute_pearson_correlation_positive():
    x = [1, 2, 3, 4, 5]
    y = [1, 2, 3, 4, 5]
    corr, p = compute_pearson_correlation(x, y)
    assert corr > 0.9
    assert p < 0.05

def test_compute_pearson_correlation_random():
    np.random.seed(42)
    x = np.random.rand(50)
    y = np.random.rand(50)
    corr, p = compute_pearson_correlation(x.tolist(), y.tolist())
    assert isinstance(corr, float)
    assert isinstance(p, float)