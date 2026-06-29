import numpy as np
import pandas as pd
from validation.compute_reliability import compute_split_half_reliability


def test_split_half_reliability_returns_float_in_range():
    """Reliability should be a float between 0 and 1 for a random dataset."""
    np.random.seed(0)
    # Create a random DataFrame with 6 marker items across 30 sessions
    df = pd.DataFrame(
        np.random.rand(30, 6),
        columns=[f"item{i+1}" for i in range(6)]
    )
    reliability = compute_split_half_reliability(df)
    assert isinstance(reliability, float), "Reliability should be a float"
    assert 0.0 <= reliability <= 1.0, "Reliability should be between 0 and 1"


def test_split_half_reliability_high_for_correlated_halves():
    """When the two halves are highly correlated, reliability should be high (>0.8)."""
    np.random.seed(1)
    # Generate two independent halves
    half1 = np.random.rand(30, 2)
    # Make the second half a noisy copy of the first half
    noise = np.random.normal(loc=0.0, scale=0.01, size=(30, 2))
    half2 = half1 + noise
    df = pd.DataFrame(
        np.hstack([half1, half2]),
        columns=["item1", "item2", "item3", "item4"]
    )
    reliability = compute_split_half_reliability(df)
    assert reliability > 0.8, f"Expected high reliability, got {reliability}"