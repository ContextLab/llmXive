import pandas as pd
from pathlib import Path
import pytest

def test_memory_nodes_parquet_verification():
    """
    Verify that the preprocessed parquet file meets the requirements:
    - Contains >= 100 rows.
    - Contains all required columns.
    - is_rare column contains a mix of True and False.
    """
    parquet_path = Path("data/processed/memory_nodes.parquet")
    assert parquet_path.is_file(), f"Parquet file not found at {parquet_path}"

    df = pd.read_parquet(parquet_path, engine="pyarrow")

    # 1. Check row count
    assert len(df) >= 100, f"Expected >= 100 rows, got {len(df)}"

    # 2. Check columns
    required_cols = {"node_id", "timestamp", "event_label", "embedding", "is_rare"}
    assert required_cols.issubset(set(df.columns)), \
        f"Missing columns. Expected {required_cols}, got {set(df.columns)}"

    # 3. Check is_rare mix
    unique_rare_values = df["is_rare"].unique()
    assert True in unique_rare_values and False in unique_rare_values, \
        f"is_rare column must contain both True and False, got {unique_rare_values}"

    # 4. Check embedding type (should be bytes)
    assert isinstance(df["embedding"].iloc[0], bytes), "embedding column should contain bytes"