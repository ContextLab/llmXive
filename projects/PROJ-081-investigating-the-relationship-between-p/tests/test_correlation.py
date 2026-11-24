"""
test_correlation.py
--------------------
Unit tests for the correlation analysis module.
"""

import numpy as np
import pandas as pd
import pytest

from code.src.correlation_analysis import compute_correlations

METABOLITE_COLUMNS = ["alkaloids", "terpenes", "phenolics", "benzoxazinoids"]

@pytest.fixture
def synthetic_data_negative():
    """Create a synthetic dataset where all metabolites are negatively correlated."""
    n = 100
    rng = np.random.default_rng(42)
    herb = rng.normal(0, 1, size=n)
    data = {
        "herbivory_score": herb,
    }
    for met in METABOLITE_COLUMNS:
        # Create a negative correlation by subtracting a scaled version of herb
        data[met] = -0.5 * herb + rng.normal(0, 0.1, size=n)
    return pd.DataFrame(data)

@pytest.fixture
def synthetic_data_insufficient():
    """Dataset designed to yield only two significant negative correlations."""
    n = 100
    rng = np.random.default_rng(1)
    herb = rng.normal(0, 1, size=n)
    data = {"herbivory_score": herb}
    # Two metabolites strongly negative, two weak/no correlation
    data["alkaloids"] = -0.6 * herb + rng.normal(0, 0.2, size=n)
    data["terpenes"] = -0.6 * herb + rng.normal(0, 0.2, size=n)
    data["phenolics"] = rng.normal(0, 1, size=n)
    data["benzoxazinoids"] = rng.normal(0, 1, size=n)
    return pd.DataFrame(data)

def test_compute_correlations_success(synthetic_data_negative):
    """Expect successful computation with 3‑5 significant negative classes."""
    result = compute_correlations(synthetic_data_negative)
    assert result["result_type"] == "correlation"
    # All four metabolites should be present
    assert set(result["matrix"].keys()) == set(METABOLITE_COLUMNS)
    # Significant negative classes must be between 3 and 5
    sig = result["significant_negative_classes"]
    assert 3 <= len(sig) <= 5

def test_compute_correlations_fails_when_out_of_range():
    """When the number of significant negative classes is not 3‑5, a ValueError is raised."""
    df = synthetic_data_insufficient()
    with pytest.raises(ValueError):
        compute_correlations(df)
