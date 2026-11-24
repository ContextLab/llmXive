"""
Unit tests for the multiscale entropy implementation.
"""
import numpy as np
import pandas as pd
import pytest

from code.src.analysis.entropy import multiscale_entropy

@pytest.fixture
def synthetic_data():
    """Create a small DataFrame with two parcels:
    - ``parcel_low``: low‑complexity sine wave.
    - ``parcel_high``: high‑complexity white noise.
    """
    rng = np.random.default_rng(42)
    t = np.linspace(0, 2 * np.pi, 200)

    low_complex = np.sin(t)  # smooth, predictable
    high_complex = rng.normal(loc=0.0, scale=1.0, size=t.shape)  # random

    df = pd.DataFrame(
        {"parcel_low": low_complex, "parcel_high": high_complex}
    )
    return df

def test_entropy_ordering(synthetic_data, tmp_path, monkeypatch):
    """Low‑complexity series should yield lower entropy than high‑complexity."""
    from llmxive_toolkit import paths as original_paths

    def fake_data(*parts):
        return tmp_path.joinpath(*parts)

    monkeypatch.setattr(original_paths, "data", fake_data)

    result = multiscale_entropy(synthetic_data, scales=(1, 2, 3), m=2, r=0.15)

    assert isinstance(result, pd.Series)
    assert set(result.index) == {"parcel_low", "parcel_high"}

    low_entropy = result["parcel_low"]
    high_entropy = result["parcel_high"]
    assert not np.isnan(low_entropy)
    assert not np.isnan(high_entropy)
    assert low_entropy < high_entropy
