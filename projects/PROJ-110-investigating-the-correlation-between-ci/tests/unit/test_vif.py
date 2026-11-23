import numpy as np
import pandas as pd
import pytest
from analysis.vif import calculate_vif, flag_high_vif

def test_vif_threshold():
    """
    Verify that the VIF calculation flags at least one of a pair of highly collinear
    predictors and does not flag an independent predictor.
    """
    rng = np.random.default_rng(0)
    n = 200
    # Highly collinear predictors
    X1 = rng.normal(size=n)
    X2 = X1 * 0.99 + rng.normal(scale=0.01, size=n)  # near‑perfect linear relationship
    # Independent predictor
    X3 = rng.normal(size=n)

    df = pd.DataFrame({"X1": X1, "X2": X2, "X3": X3})

    # Compute VIFs
    vif_df = calculate_vif(df)

    # Identify features with VIF > 5
    high_vif_features = flag_high_vif(vif_df, threshold=5.0)

    # At least one of the collinear features should be flagged
    assert any(col in high_vif_features for col in ("X1", "X2")), \
        "Expected at least one collinear feature to be flagged for high VIF"

    # Independent feature should not be flagged
    assert "X3" not in high_vif_features, \
        "Independent feature X3 was incorrectly flagged as high VIF"