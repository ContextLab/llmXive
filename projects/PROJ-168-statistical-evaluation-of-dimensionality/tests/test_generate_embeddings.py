import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from llmxive_toolkit import paths

def test_embedding_files_exist():
    """Verify that embeddings were generated for all available datasets."""
    import json
    manifest_path = paths.data("manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    available = [e["dataset_id"] for e in manifest if e["status"] == "Available"]
    
    for ds in available:
        pca_file = paths.data("embeddings", f"{ds}_PCA.csv")
        tsne_file = paths.data("embeddings", f"{ds}_tSNE.csv")
        umap_file = paths.data("embeddings", f"{ds}_UMAP.csv")
        
        assert pca_file.exists()
        assert tsne_file.exists()
        assert umap_file.exists()
        
        # Verify shapes
        pca_df = pd.read_csv(pca_file)
        assert pca_df.shape[1] == 31
        assert not pca_df.isna().any().any()
        
        tsne_df = pd.read_csv(tsne_file)
        assert tsne_df.shape[1] == 3
        assert not tsne_df.isna().any().any()
        
        umap_df = pd.read_csv(umap_file)
        assert umap_df.shape[1] == 3
        assert not umap_df.isna().any().any()
        
        # Verify row counts match
        matrix_path = paths.data("processed", f"{ds}_matrix.parquet")
        matrix_df = pd.read_parquet(matrix_path)
        assert len(pca_df) == len(matrix_df)
        assert len(tsne_df) == len(matrix_df)
        assert len(umap_df) == len(matrix_df)

def test_monitoring_contains_entries():
    """Verify monitoring CSV contains embedding steps."""
    monitoring_path = paths.results("monitoring.csv")
    assert monitoring_path.exists()
    content = monitoring_path.read_text()
    assert "embed_PCA_" in content
    assert "embed_tSNE_" in content
    assert "embed_UMAP_" in content