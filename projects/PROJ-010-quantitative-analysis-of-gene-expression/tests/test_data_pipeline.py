import pytest
import scanpy as sc
import os
from llmxive_toolkit import paths

def test_integrated_atlas_exists():
    # The pipeline should produce this file
    path = paths.path("data/processed/integrated_atlas.h5ad")
    assert path.exists(), "Integrated atlas file was not created."

def test_atlas_content():
    path = paths.path("data/processed/integrated_atlas.h5ad")
    adata = sc.read_h5ad(path)
    
    # Check for required metadata
    assert 'stage' in adata.obs.columns, "Missing 'stage' annotation."
    assert 'batch' in adata.obs.columns, "Missing 'batch' annotation."
    
    # Check for processed data
    assert 'X_pca' in adata.obsm, "PCA embedding missing."
    
    # Verify gap detection constraint (implied by file existence)
    # Since the script raises RuntimeError on gaps, the file's existence 
    # implies no gaps < 10 cells were found.
    for stage in adata.obs['stage'].unique():
        count = (adata.obs['stage'] == stage).sum()
        assert count >= 10, f"Stage {stage} has insufficient cells: {count}"