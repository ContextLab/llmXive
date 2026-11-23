"""
tests/contract/test_arg_matrix_schema.py

Contract test for ``data/processed/arg_matrix.csv`` produced by
``src.pipeline.extract_baseline``.  The test verifies:

1. The CSV file exists.
2. It contains a column named ``isolate_id``.
3. It contains at least one ARG column (any column other than
   ``isolate_id`` and ``checksum``).
4. It contains a ``checksum`` column.
5. The number of rows matches the number of isolates recorded in
   ``data/processed/sample_sizes.csv``.
"""

import pathlib

import pandas as pd
import pytest

from llmxive_toolkit import paths


@pytest.fixture(scope="module")
def arg_matrix():
    """Load the ARG matrix CSV."""
    csv_path = paths.data("processed", "arg_matrix.csv")
    assert csv_path.is_file(), f"ARG matrix not found at {csv_path}"
    return pd.read_csv(csv_path)


@pytest.fixture(scope="module")
def sample_sizes():
    """Load the sample‑size CSV produced by the download step."""
    csv_path = paths.data("processed", "sample_sizes.csv")
    assert csv_path.is_file(), f"sample_sizes.csv not found at {csv_path}"
    return pd.read_csv(csv_path)


def test_columns_present(arg_matrix):
    """Check required columns exist."""
    cols = set(arg_matrix.columns)
    assert "isolate_id" in cols, "Missing required column 'isolate_id'."
    assert "checksum" in cols, "Missing required column 'checksum'."

    # Any column besides isolate_id and checksum is considered an ARG column
    arg_cols = cols - {"isolate_id", "checksum"}
    assert arg_cols, "ARG matrix contains no ARG columns."


def test_row_count_matches(arg_matrix, sample_sizes):
    """Row count must equal the number of isolates in sample_sizes.csv."""
    isolates_in_matrix = set(arg_matrix["isolate_id"].astype(str))
    isolates_in_samples = set(sample_sizes["isolate_id"].astype(str))
    assert isolates_in_matrix == isolates_in_samples, (
        "Mismatch between isolates in arg_matrix.csv and sample_sizes.csv.\n"
        f"  In matrix only: {sorted(isolates_in_matrix - isolates_in_samples)}\n"
        f"  In sample_sizes only: {sorted(isolates_in_samples - isolates_in_matrix)}"
    )