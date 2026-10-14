"""
Tests for the ``load_parquet_as_df`` helper.
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

from loaders import load_parquet_as_df


def test_load_parquet_as_df(tmp_path: Path):
    # Create a small DataFrame and write it as Parquet
    df_original = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parquet_file = tmp_path / "test.parquet"
    df_original.to_parquet(parquet_file)

    # Use the loader to read it back
    df_loaded = load_parquet_as_df(parquet_file)

    pd.testing.assert_frame_equal(df_original, df_loaded)