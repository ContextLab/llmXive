"""
Unit tests for the preprocess module.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import preprocess_data, calculate_missing_ratio, MISSING_THRESHOLD

def create_test_csv(path: Path, missing_ratio: float = 0.0, rows: int = 100):
    """Helper to create test CSV with specific missingness."""
    data = {
        "id": range(rows),
        "pre_self_esteem": np.random.normal(50, 10, rows),
        "post_self_esteem": np.random.normal(52, 10, rows),
        "comparison_tendency": np.random.normal(30, 5, rows),
        "avatar_condition": np.random.choice([0, 1], rows)
    }
    df = pd.DataFrame(data)

    if missing_ratio > 0:
        # Randomly introduce NaNs
        total_cells = df.size
        num_missing = int(total_cells * missing_ratio)
        missing_indices = np.random.choice(total_cells, num_missing, replace=False)
        flat_df = df.values.flatten()
        flat_df[missing_indices] = np.nan
        df = pd.DataFrame(flat_df.reshape(df.shape), columns=df.columns)
        # Convert back to numeric
        df["pre_self_esteem"] = pd.to_numeric(df["pre_self_esteem"], errors="coerce")
        df["post_self_esteem"] = pd.to_numeric(df["post_self_esteem"], errors="coerce")
        df["comparison_tendency"] = pd.to_numeric(df["comparison_tendency"], errors="coerce")

    df.to_csv(path, index=False)
    return df

def test_low_missingness_imputation():
    """Test that data with < 20% missingness gets imputed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input_low.csv"
        output_path = Path(tmpdir) / "output_low.csv"

        create_test_csv(input_path, missing_ratio=0.10, rows=100)
        df_result, stats = preprocess_data(input_path, output_path)

        assert stats["imputed"] is True
        assert stats["method"] in ["miceforest", "sklearn_iterative"]
        assert df_result is not None
        assert output_path.exists()
        # Check no NaNs in numeric cols
        numeric_cols = df_result.select_dtypes(include=[np.number]).columns
        assert df_result[numeric_cols].isnull().sum().sum() == 0

def test_high_missingness_row_drop():
    """Test that rows with > 20% missingness are dropped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input_high.csv"
        output_path = Path(tmpdir) / "output_high.csv"

        # Create data with high missingness, but ensure some rows are clean
        # We need to force row-wise missingness > 20%
        # 5 cols. 20% of 5 is 1. So if a row has 2+ NaNs, it should be dropped?
        # Wait, 20% of 5 is 1. So > 1 missing means > 20%.
        # Let's create a dataset where half the rows have 3 NaNs (60%)
        rows = 100
        data = {
            "id": range(rows),
            "pre_self_esteem": np.random.normal(50, 10, rows),
            "post_self_esteem": np.random.normal(52, 10, rows),
            "comparison_tendency": np.random.normal(30, 5, rows),
            "avatar_condition": np.random.choice([0, 1], rows)
        }
        df = pd.DataFrame(data)

        # Force high missingness on first 50 rows (2 NaNs each -> 40% > 20%)
        for i in range(50):
            df.loc[i, "pre_self_esteem"] = np.nan
            df.loc[i, "post_self_esteem"] = np.nan

        df.to_csv(input_path, index=False)

        df_result, stats = preprocess_data(input_path, output_path)

        # Should have dropped ~50 rows
        assert len(df_result) < 100
        assert stats["rows_dropped"] > 0
        # The remaining rows should be imputed if they have any missing, or just passed through
        # Since we dropped the bad ones, the remaining ones are clean (0 missing)
        # So imputed might be False if no missing left
        assert output_path.exists()

def test_all_rows_dropped_error():
    """Test that an error is raised if all rows are dropped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input_all_bad.csv"
        output_path = Path(tmpdir) / "output_all_bad.csv"

        rows = 10
        data = {
            "id": range(rows),
            "pre_self_esteem": [np.nan] * rows,
            "post_self_esteem": [np.nan] * rows,
            "comparison_tendency": [np.nan] * rows,
            "avatar_condition": [np.nan] * rows
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)

        with pytest.raises(ValueError, match="All rows dropped"):
            preprocess_data(input_path, output_path)

def test_no_missingness():
    """Test data with no missingness passes through."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input_clean.csv"
        output_path = Path(tmpdir) / "output_clean.csv"

        create_test_csv(input_path, missing_ratio=0.0, rows=50)
        df_result, stats = preprocess_data(input_path, output_path)

        assert stats["imputed"] is False
        assert stats["method"] == "none"
        assert len(df_result) == 50
        assert output_path.exists()
