import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from descriptors import calculate_weighted_mean_variance


def test_calculate_weighted_mean_variance():
    """Test weighted mean and variance calculation."""
    # Create a simple properties DataFrame
    props_df = pd.DataFrame(
        {
            "element": ["Fe", "O", "C"],
            "electronegativity": [1.83, 3.44, 2.55],
        }
    )

    mean, var = calculate_weighted_mean_variance("Fe2O3", props_df, "electronegativity")

    # Fe2O3: 2 Fe, 3 O
    # Total weight: 5
    # Mean: (2*1.83 + 3*3.44) / 5 = (3.66 + 10.32) / 5 = 13.98 / 5 = 2.796
    expected_mean = (2 * 1.83 + 3 * 3.44) / 5
    assert np.isclose(mean, expected_mean, rtol=1e-5)

    # Variance: sum(w * (x - mean)^2) / sum(w)
    expected_var = (
        2 * (1.83 - expected_mean) ** 2 + 3 * (3.44 - expected_mean) ** 2
    ) / 5
    assert np.isclose(var, expected_var, rtol=1e-5)


def test_missing_element():
    """Test handling of missing element."""
    props_df = pd.DataFrame(
        {
            "element": ["Fe"],
            "electronegativity": [1.83],
        }
    )

    mean, var = calculate_weighted_mean_variance("FeO", props_df, "electronegativity")

    # O is missing, so only Fe is used
    assert np.isclose(mean, 1.83)
    assert var == 0.0
