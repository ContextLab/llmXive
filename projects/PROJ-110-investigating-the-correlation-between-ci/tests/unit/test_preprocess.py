"""
Unit tests for the ``log_transform_expression`` function.

The tests create a temporary TPM matrix, invoke the transformation,
and verify that the output matches the expected log2(TPM + 1) values.
"""

import math
from pathlib import Path

import pandas as pd
import pytest

from data.preprocess import log_transform_expression

@pytest.fixture
def sample_matrix(tmp_path: Path) -> Path:
    """
    Write a tiny TPM matrix to ``tmp_path`` and return its path.
    The matrix contains two genes (rows) and three samples (columns).
    """
    df = pd.DataFrame(
        {
            "sample_A": [0, 5, 10],
            "sample_B": [2, 0, 20],
            "sample_C": [3, 15, 0],
        },
        index=["GENE1", "GENE2", "GENE3"],
    )
    # The first column (index) will be saved as the gene identifier.
    out_path = tmp_path / "core_genes_matrix.csv"
    df.to_csv(out_path)
    return out_path

def test_log_transform_creates_correct_output(tmp_path: Path, sample_matrix: Path):
    """
    Verify that the log‑transformed CSV is created and contains the correct values.
    """
    output_path = tmp_path / "core_genes_log2_matrix.csv"

    # Run the transformation using the temporary files.
    result_path = log_transform_expression(
        input_path=sample_matrix,
        output_path=output_path,
        pseudocount=1.0,
    )

    # The function should return the exact output path we supplied.
    assert result_path == output_path
    assert result_path.is_file()

    # Load the result and compare against the analytical expectation.
    df_out = pd.read_csv(result_path, index_col=0)

    # Re‑compute expected values directly.
    df_expected = (pd.read_csv(sample_matrix, index_col=0) + 1).applymap(
        lambda x: math.log2(x)
    )

    # Use pandas testing utilities for a column‑wise numeric comparison.
    pd.testing.assert_frame_equal(df_out, df_expected, rtol=1e-12, atol=1e-12)

def test_missing_input_raises(tmp_path: Path):
    """
    The function must raise ``FileNotFoundError`` when the input does not exist.
    """
    missing_path = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        log_transform_expression(input_path=missing_path, output_path=tmp_path / "out.csv")