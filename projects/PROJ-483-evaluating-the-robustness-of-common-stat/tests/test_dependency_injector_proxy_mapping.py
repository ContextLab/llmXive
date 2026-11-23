import numpy as np
import pytest
from dependency_injector import generate_spatial_proxy, proxy_to_r

def test_proxy_to_r_mapping():
    # Create simple 2‑D data where clustering is obvious
    rng = np.random.default_rng(0)
    cluster1 = rng.normal(loc=0.0, scale=0.5, size=(50, 2))
    cluster2 = rng.normal(loc=5.0, scale=0.5, size=(50, 2))
    data = np.vstack([cluster1, cluster2])

    proxy = generate_spatial_proxy(data, n_clusters=2, seed=42)
    r = proxy_to_r(data, proxy)

    # Silhouette for well‑separated clusters should be high (>0.5)
    assert 0.5 < r <= 1.0, f"Expected r in (0.5,1], got {r}"