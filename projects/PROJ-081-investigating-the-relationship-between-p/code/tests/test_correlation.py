import numpy as np
import pandas as pd
import pytest

from src.correlation_analysis import compute_correlations


@pytest.fixture
def synthetic_data_negative():
    """Create a synthetic dataset where all metabolites are negatively correlated
    with herbivory_score and should produce 4 significant negative classes."""
    np.random.seed(0)
    n = 200
    # Generate metabolites with standard normal distribution
    alk = np.random.normal(0, 1, n)
    ter = np.random.normal(0, 1, n)
    phe = np.random.normal(0, 1, n)
    ben = np.random.normal(0, 1, n)

    # Herbivory score strongly negatively related to the sum of metabolites
    herb = -(alk + ter + phe + ben) + np.random.normal(0, 0.5, n)

    df = pd.DataFrame({
        "alkaloids": alk,
        "terpenes": ter,
        "phenolics": phe,
        "benzoxazinoids": ben,
        "herbivory_score": herb,
    })
    return df


@pytest.fixture
def synthetic_data_insufficient():
    """Dataset designed to yield only two significant negative correlations."""
    np.random.seed(1)
    n = 200
    alk = np.random.normal(0, 1, n)
    ter = np.random.normal(0, 1, n)
    phe = np.random.normal(0, 1, n)
    ben = np.random.normal(0, 1, n)

    # Make herbivory strongly related to alk and ter only
    herb = -(alk + ter) + np.random.normal(0, 1.5, n)

    df = pd.DataFrame({
        "alkaloids": alk,
        "terpenes": ter,
        "phenolics": phe,
        "benzoxazinoids": ben,
        "herbivory_score": herb,
    })
    return df


def test_compute_correlations_success(synthetic_data_negative):
    """Expect successful computation with 3‑5 significant negative classes."""
    result = compute_correlations(synthetic_data_negative)

    # Coefficients must be within [-1, 1] and negative
    for coeff in result["matrix"].values():
        assert -1.0 <= coeff <= 0.0

    # p‑values and q‑values within [0, 1]
    for p in result["p_values"].values():
        assert 0.0 <= p <= 1.0
    for q in result["q_values"].values():
        assert 0.0 <= q <= 1.0

    # Length of significant_negative_classes must be between 3 and 5
    assert 3 <= len(result["significant_negative_classes"]) <= 5


def test_compute_correlations_fails_when_out_of_range():
    """When the number of significant negative classes is not 3‑5, a ValueError is raised."""
    df = pd.DataFrame({
        "alkaloids": [1, 2, 3],
        "terpenes": [1, 2, 3],
        "phenolics": [1, 2, 3],
        "benzoxazinoids": [1, 2, 3],
        "herbivory_score": [10, 11, 12],
    })
    # This tiny dataset will yield perfect positive correlation, so no negative classes
    with pytest.raises(ValueError):
        compute_correlations(df)