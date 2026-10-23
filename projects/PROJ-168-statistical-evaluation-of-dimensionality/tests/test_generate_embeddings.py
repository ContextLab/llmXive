"""
Unit tests for the generate_embeddings script (T009).

The tests verify that the script can be imported and that the
``main`` function runs without error on a minimal synthetic
dataset.  Real data are not required; the test creates a tiny
processed matrix, writes it to the expected location, runs the
script and checks that the three embedding CSV files are created
and have the correct shapes.
"""

import os
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

import pytest

# Import the script as a module
from generate_embeddings import main as generate_main, _load_manifest, _load_processed_matrix

@pytest.fixture
def minimal_manifest(tmp_path):
    """Create a minimal manifest.json with a single synthetic dataset."""
    manifest = [
        {
            "dataset_id": "TEST001",
            "source_url": "https://example.org/fake",
            "status": "Available",
            "checksum": "dummy",
            "raw_file_path": str(tmp_path / "raw" / "TEST001.h5ad"),
            "processed_file_path": None
        }
    ]
    manifest_path = Path("data/manifest.json")
    # Ensure the data directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    return manifest

@pytest.fixture
def synthetic_processed_matrix(tmp_path):
    """Write a tiny processed matrix parquet file."""
    n_cells = 20
    n_genes = 10
    np.random.seed(42)
    data = np.random.randn(n_cells, n_genes)
    cell_ids = [f"cell_{i}" for i in range(n_cells)]
    df = pd.DataFrame(data, columns=[f"gene_{i}" for i in range(n_genes)])
    df.insert(0, "cell_id", cell_ids)
    matrix_path = Path("data/processed/TEST001_matrix.parquet")
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(matrix_path)
    return matrix_path

def test_load_manifest(minimal_manifest):
    manifest = _load_manifest()
    assert isinstance(manifest, list)
    assert manifest[0]["dataset_id"] == "TEST001"

def test_load_processed_matrix(synthetic_processed_matrix):
    df = _load_processed_matrix("TEST001")
    assert "cell_id" in df.columns
    assert df.shape[0] == 20
    assert df.shape[1] == 11  # 10 genes + cell_id

def test_full_embedding_generation(tmp_path, minimal_manifest, synthetic_processed_matrix):
    """
    Run the script's main() and verify that the three CSV files are
    created with the expected number of rows and columns.
    """
    # Ensure the embeddings directory exists
    embeddings_dir = Path("data/embeddings")
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    # Run the script
    exit_code = generate_main()
    assert exit_code == 0

    # Check PCA output
    pca_path = embeddings_dir / "TEST001_PCA.csv"
    assert pca_path.is_file()
    pca_df = pd.read_csv(pca_path)
    assert pca_df.shape[0] == 20
    # cell_id + 30 PCs = 31 columns
    assert pca_df.shape[1] == 31
    assert not pca_df.isnull().any().any()

    # Check t‑SNE output
    tsne_path = embeddings_dir / "TEST001_tSNE.csv"
    assert tsne_path.is_file()
    tsne_df = pd.read_csv(tsne_path)
    assert tsne_df.shape[0] == 20
    # cell_id + 2 dims = 3 columns
    assert tsne_df.shape[1] == 3
    assert not tsne_df.isnull().any().any()

    # Check UMAP output
    umap_path = embeddings_dir / "TEST001_UMAP.csv"
    assert umap_path.is_file()
    umap_df = pd.read_csv(umap_path)
    assert umap_df.shape[0] == 20
    assert umap_df.shape[1] == 3
    assert not umap_df.isnull().any().any()

    # Verify that monitoring.csv now contains the three new steps
    monitoring_path = Path("results/monitoring.csv")
    assert monitoring_path.is_file()
    monitoring_df = pd.read_csv(monitoring_path)
    expected_steps = {
        "embed_PCA_TEST001",
        "embed_tSNE_TEST001",
        "embed_UMAP_TEST001",
    }
    assert expected_steps.issubset(set(monitoring_df["step"]))