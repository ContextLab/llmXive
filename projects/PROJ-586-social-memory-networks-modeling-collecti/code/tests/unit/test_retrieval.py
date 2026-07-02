import pytest
from metrics.retrieval import compute_retrieval_efficiency

def test_valid_efficiency():
    metrics, eff = compute_retrieval_efficiency(5, 10, 5)
    assert isinstance(metrics, dict)
    assert isinstance(eff, float)
    assert metrics["retrieval_efficiency"] == eff

def test_invalid_inputs():
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(5, 10, -1)
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(5, -1, 3)
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(-1, 10, 3)
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(15, 10, 3)  # retrieved > total
