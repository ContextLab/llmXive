"""
Unit test for T019 – extract_features.py

The test runs the extraction helper with a tiny GSM8K subset and a very
small model (distilgpt2). It verifies that:

* The Parquet file is created.
* The required columns exist and contain numeric data.
* Re‑running the extraction with the same seed produces byte‑identical
  Parquet files (deterministic behaviour).
"""

import filecmp
from pathlib import Path

import pandas as pd
import pytest

# Import the helper directly from the module under test.
from code.data.extract_features import run_extraction

@pytest.mark.timeout(300)
def test_extract_features_deterministic(tmp_path: Path):
    # Define output locations inside the repository's data folder.
    output_path_1 = Path("data/processed/test_features_1.parquet")
    output_path_2 = Path("data/processed/test_features_2.parquet")

    # Ensure a clean start.
    if output_path_1.is_file():
        output_path_1.unlink()
    if output_path_2.is_file():
        output_path_2.unlink()

    # First run.
    df1 = run_extraction(
        model_name="distilgpt2",
        sample_size=5,
        output_path=output_path_1,
        seed=123,
        apply_pca=False,
    )
    # Second run with the same seed.
    df2 = run_extraction(
        model_name="distilgpt2",
        sample_size=5,
        output_path=output_path_2,
        seed=123,
        apply_pca=False,
    )

    # -----------------------------------------------------------------
    # Verify file creation and schema.
    # -----------------------------------------------------------------
    assert output_path_1.is_file(), "First Parquet output missing"
    assert output_path_2.is_file(), "Second Parquet output missing"

    required_columns = {"input_id", "gradient_norm", "local_curvature"}
    assert required_columns.issubset(df1.columns), "Missing expected columns in first run"
    assert required_columns.issubset(df2.columns), "Missing expected columns in second run"

    # Verify numeric dtypes.
    for col in ["gradient_norm", "local_curvature"]:
        assert pd.api.types.is_numeric_dtype(df1[col]), f"{col} not numeric in first run"
        assert pd.api.types.is_numeric_dtype(df2[col]), f"{col} not numeric in second run"

    # -----------------------------------------------------------------
    # Determinism: the two Parquet files must be byte‑identical.
    # -----------------------------------------------------------------
    assert filecmp.cmp(str(output_path_1), str(output_path_2), shallow=False), "Parquet files differ despite same seed"

    # Clean up after the test.
    output_path_1.unlink()
    output_path_2.unlink()
