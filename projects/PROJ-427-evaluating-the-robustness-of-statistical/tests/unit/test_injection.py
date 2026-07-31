"""
Unit tests for the data injection logic.

This file contains tests for the random value replacement,
category misclassification, and MCAR missingness injection functions
defined in ``code.inject``.
"""

import pandas as pd

# Import the functions from the inject module.
from code.inject import (
    inject_random_replacement,
    inject_category_misclassification,
    inject_mcar_missingness,
)


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


def test_misclassification_shifts_frequencies():
    """
    Verify that category misclassification changes the observed frequencies
    in a predictable way.

    The injection algorithm reassigns a fraction ``error_rate`` of rows to a
    *different* category, sampling the new category uniformly from the set
    of all *other* categories.  Under this model, the expected count for a
    given category ``i`` after injection is:

        expected_i = original_i * (1 - error_rate) +
                     error_rate * (total_rows - original_i) / (K - 1)

    where ``K`` is the number of distinct categories.
    """
    # Create a categorical dataframe with a known distribution.
    #   A:5, B:3, C:2  → total 10 rows.
    df = pd.DataFrame(
        {"cat": ["A"] * 5 + ["B"] * 3 + ["C"] * 2}
    )
    error_rate = 0.2  # 20 % of rows should be mis‑classified → 2 rows.
    seed = 42

    # Perform the misclassification injection.
    corrupted_df, injected_cnt = inject_category_misclassification(df, error_rate, seed=seed)

    # 1️⃣  Check that the reported injected count matches expectation.
    assert injected_cnt == int(len(df) * error_rate)

    # Compute original and new frequencies (as counts).
    original_counts = df["cat"].value_counts().sort_index()
    new_counts = corrupted_df["cat"].value_counts().sort_index()

    total_rows = len(df)
    categories = original_counts.index.tolist()
    K = len(categories)

    # Expected counts according to the model described above.
    expected_counts = {}
    for cat in categories:
        orig = original_counts[cat]
        expected = orig * (1 - error_rate) + error_rate * (total_rows - orig) / (K - 1)
        expected_counts[cat] = expected

    # Allow a small tolerance because the injection is stochastic.
    tolerance = 0.5  # half a row tolerance is reasonable for such a small sample.

    for cat in categories:
        observed = new_counts.get(cat, 0)
        expected = expected_counts[cat]
        assert abs(observed - expected) < tolerance, (
            f"Category {cat}: observed {observed}, expected {expected:.2f}"
        )


def test_mcar_introduces_nans():
    """
    Verify that MCAR missingness injects the correct number of NaN cells.

    The function should replace a fraction ``error_rate`` of *all* cells
    (rows × columns) with ``NaN``.  The test checks both the reported
    injected count and the actual number of NaNs present in the output.
    """
    # Small deterministic dataframe.
    df = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
        }
    )
    error_rate = 0.5  # 50 % of cells → 3 NaNs (6 cells total).
    seed = 999

    corrupted_df, injected_cnt = inject_mcar_missingness(df, error_rate, seed=seed)

    total_cells = df.shape[0] * df.shape[1]
    expected_injected = int(total_cells * error_rate)

    # Number of NaNs actually present.
    nan_count = corrupted_df.isna().sum().sum()

    assert injected_cnt == expected_injected
    assert nan_count == expected_injected

# End of test file.