"""
Unit test for the VIF computation added in T037.

The test constructs a tiny synthetic dataset where the two predictors are
perfectly collinear (braid_index = 2 * crossing_number).  In that case the
VIF for each predictor should be large (>> 1).  The test verifies that the
``compute_vif`` function runs without error and returns a DataFrame containing
the expected columns.
"""

import pandas as pd
import pytest

from analysis.regression import compute_vif


@pytest.fixture
def collinear_dataframe():
    # Create a small dataset with perfect collinearity
    data = {
        "crossing_number": [1, 2, 3, 4, 5],
        "braid_index": [2, 4, 6, 8, 10],
        "hyperbolic_volume": [0.5, 1.0, 1.5, 2.0, 2.5],
    }
    return pd.DataFrame(data)


def test_compute_vif_returns_dataframe(collinear_dataframe):
    vif_df = compute_vif(collinear_dataframe, ["crossing_number", "braid_index"])
    # Verify shape and columns
    assert isinstance(vif_df, pd.DataFrame)
    assert set(vif_df.columns) == {"feature", "vif"}
    # Both features should be present
    assert set(vif_df["feature"]) == {"crossing_number", "braid_index"}
    # VIF values should be greater than 1 (indicative of multicollinearity)
    assert all(vif_df["vif"] > 1.0)