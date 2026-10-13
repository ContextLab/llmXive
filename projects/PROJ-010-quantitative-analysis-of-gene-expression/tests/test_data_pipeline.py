"""
Basic sanity tests for the data pipeline core module.
"""

import os
from pathlib import Path

import pytest
import scanpy as sc

from code.data_pipeline import main as pipeline_main

@pytest.fixture(scope="module")
def output_path(tmp_path_factory):
    """Temporary path for the integrated AnnData output."""
    return tmp_path_factory.mktemp("output") / "integrated_atlas.h5ad"

def test_pipeline_runs_and_produces_output(output_path):
    """The pipeline should run without error and write an .h5ad file."""
    # Simulate command‑line arguments
    import sys

    original_argv = sys.argv.copy()
    try:
        sys.argv = [
            "code/data_pipeline.py",
            "--dataset",
            "fetal_brain_atlas",
            "--output",
            str(output_path),
        ]
        pipeline_main()
    finally:
        sys.argv = original_argv

    assert output_path.is_file(), "Output .h5ad file was not created"
    # Load and perform a minimal sanity check
    adata = sc.read_h5ad(output_path)
    assert adata.n_obs > 0, "No cells in the output AnnData"
    assert "X_pca_harmony" in adata.obsm, "Harmony‑corrected PCA missing"