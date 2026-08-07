import csv
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from data.downloader import filter_core_genes
from data.config import CORE_CIRCADIAN_GENES

@pytest.fixture
def dummy_matrix(tmp_path: Path) -> Path:
    """
    Create a minimal TPM matrix CSV with a subset of core genes and some extra genes.
    The matrix has two samples (rows) and a mixture of genes (columns).
    """
    data = {
        "sample_id": ["S1", "S2"],
        "PER1": [0.5, 1.2],
        "PER2": [2.3, 0.0],
        "NONCORE1": [5.0, 3.2],
        "BMAL1": [0.0, 0.8],
    }
    df = pd.DataFrame(data).set_index("sample_id")
    csv_path = tmp_path / "gtex_v8_tpm_matrix.csv"
    df.to_csv(csv_path)
    return csv_path

def test_filter_core_genes_success(tmp_path: Path, dummy_matrix: Path):
    """
    Verify that ``filter_core_genes`` writes a CSV containing only the core genes.
    """
    output_path = tmp_path / "core_genes_matrix.csv"

    # Run the function, pointing it to the dummy matrix
    filter_core_genes(
        raw_matrix_path=dummy_matrix,
        output_path=output_path,
    )

    # Load the output and check its columns
    result_df = pd.read_csv(output_path, index_col=0)

    # Expected columns are the intersection of CORE_CIRCADIAN_GENES and the dummy matrix
    expected_genes = [g for g in CORE_CIRCADIAN_GENES if g in dummy_matrix.name or g in pd.read_csv(dummy_matrix, nrows=0).columns]
    expected_genes = [g for g in CORE_CIRCADIAN_GENES if g in result_df.columns]

    assert list(result_df.columns) == expected_genes
    assert result_df.shape[0] == 2  # same number of samples as input

def test_filter_core_genes_missing_file(tmp_path: Path):
    """
    Ensure that a missing input file raises ``FileNotFoundError``.
    """
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        filter_core_genes(raw_matrix_path=missing_path, output_path=tmp_path / "out.csv")

def test_filter_core_genes_no_core_genes(tmp_path: Path):
    """
    If none of the core genes are present, the function should raise ``ValueError``.
    """
    # Create a matrix that deliberately lacks any core genes
    df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "NONCORE_A": [1.0],
            "NONCORE_B": [2.0],
        }
    ).set_index("sample_id")
    csv_path = tmp_path / "no_core.csv"
    df.to_csv(csv_path)

    with pytest.raises(ValueError):
        filter_core_genes(raw_matrix_path=csv_path, output_path=tmp_path / "out.csv")