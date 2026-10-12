"""
Contract test for the baseline TDA feature matrix (10×10 persistence images).

Verifies:
1. The CSV exists.
2. It contains the same number of rows as ``filtered_esol.csv``.
3. No NaN values are present.
"""
import pandas as pd
from pathlib import Path

def test_tda_feature_matrix():
    processed_dir = Path("data") / "processed"
    tda_path = processed_dir / "persistence_images_10x10.csv"
    filtered_path = processed_dir / "filtered_esol.csv"

    # Ensure files exist
    assert tda_path.is_file(), f"{tda_path} does not exist"
    assert filtered_path.is_file(), f"{filtered_path} does not exist"

    tda_df = pd.read_csv(tda_path)
    filtered_df = pd.read_csv(filtered_path)

    # Row count must match
    assert (
        len(tda_df) == len(filtered_df)
    ), f"Row count mismatch: {len(tda_df)} vs {len(filtered_df)}"

    # No NaNs
    assert not tda_df.isnull().any().any(), "NaN values found in TDA feature matrix"