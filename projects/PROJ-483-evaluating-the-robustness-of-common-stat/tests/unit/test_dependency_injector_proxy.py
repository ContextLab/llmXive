import numpy as np
import pytest

from dependency_injector import generate_spatial_proxy, validate_feature_space_proxy

def test_generate_proxy_k3():
    """
    Verify that the proxy generation uses exactly three clusters.
    """
    rng = np.random.RandomState(0)
    data = rng.randn(150, 4)  # 150 samples, 4 features
    proxy = generate_spatial_proxy(data, n_clusters=3, seed=123)
    assert proxy["n_clusters"] == 3
    labels = np.array(proxy["labels"])
    assert set(labels) == {0, 1, 2}
    # Basic sanity: number of labels must equal number of samples
    assert len(labels) == data.shape[0]

def test_proxy_validation_passes():
    """
    The validation should mark the proxy as valid for well‑behaved data.
    """
    rng = np.random.RandomState(1)
    data = rng.randn(120, 2)
    proxy = generate_spatial_proxy(data, n_clusters=3, seed=7)
    result = validate_feature_space_proxy(proxy, data)
    assert result["valid"] is True
    # No errors should be reported
    assert result["errors"] == []