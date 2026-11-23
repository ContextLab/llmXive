"""
Test that the data preprocessing pipeline produces a valid AnnData file.
"""
import pathlib

import scanpy as sc
import pytest

from llmxive_toolkit import paths

@pytest.fixture(scope="session")
def output_path():
    # The pipeline should have written this file during the quickstart run.
    return paths.data("processed", "integrated_atlas.h5ad")

def test_output_file_exists(output_path: pathlib.Path):
    assert output_path.is_file(), f"Expected output file not found: {output_path}"

def test_output_is_ann_data(output_path: pathlib.Path):
    # Attempt to read the file with Scanpy; will raise if not a valid AnnData.
    adata = sc.read_h5ad(output_path)
    assert adata.n_obs > 0, "AnnData contains no cells"
    assert adata.n_vars > 0, "AnnData contains no genes"