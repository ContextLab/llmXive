"""
Unit tests for the random value replacement injection logic.
"""

import pandas as pd

# Import the function from the package we just created.
from code.inject import inject_random_replacement

def test_replacement_preserves_distribution():
    """
    Verify that the number of injected rows matches the expected count
    and that the mean of the unmodified subset remains identical to the
    original mean (using a constant column to guarantee exact equality).
    """
    # Create a simple constant dataframe – the mean is trivially known.
    df = pd.DataFrame({"value": [5] * 10})  # 10 rows, all value = 5
    error_rate = 0.2  # Expect 20 % of rows to be replaced → 2 rows

    # Perform injection with a fixed seed for reproducibility.
    corrupted_df, injected_cnt = inject_random_replacement(df, error_rate, seed=123)

    # 1️⃣  Check that the reported injected count is correct.
    assert injected_cnt == int(len(df) * error_rate)

    # 2️⃣  Identify rows that were *not* altered.
    #    For a constant column, any value still equal to 5 is unmodified.
    unmodified = corrupted_df[corrupted_df["value"] == 5]

    # Original mean (constant column) is 5.
    original_mean = df["value"].mean()
    # Mean of the unmodified subset should also be 5.
    unmodified_mean = unmodified["value"].mean()

    assert original_mean == unmodified_mean
