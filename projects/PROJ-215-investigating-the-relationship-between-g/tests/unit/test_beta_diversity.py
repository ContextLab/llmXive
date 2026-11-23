import os
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from code.preprocessing import generate_beta_diversity_matrices, filter_low_prevalence, apply_vst

def test_filter_low_prevalence():
    """Test filtering of low prevalence taxa."""
    counts = np.array([
        [10, 0, 5],
        [0, 0, 2],
        [5, 1, 3]
    ])
    # Taxon 1 (index 1) has prevalence 1/3 < 0.5
    # Taxon 0 and 2 have prevalence > 0.5
    filtered = filter_low_prevalence(counts, threshold=0.5)
    assert filtered.shape[1] == 2
    assert np.array_equal(filtered[:, 0], [10, 0, 5])
    assert np.array_equal(filtered[:, 1], [5, 2, 3])

def test_apply_vst():
    """Test VST transformation."""
    counts = np.array([[10, 0], [5, 1]])
    transformed = apply_vst(counts)
    assert transformed.shape == counts.shape
    assert not np.any(np.isnan(transformed))

def test_generate_beta_diversity_matrices_no_tree():
    """Test beta diversity generation without a tree (Bray-Curtis only)."""
    counts = np.array([
        [10, 5, 2],
        [0, 2, 8],
        [5, 5, 5]
    ])
    metadata = pd.DataFrame({
        "sample_id": ["S1", "S2", "S3"]
    }, index=["S1", "S2", "S3"])
    
    matrices = generate_beta_diversity_matrices(counts, metadata)
    
    assert "braycurtis" in matrices
    assert "weighted_unifrac" not in matrices
    assert "unweighted_unifrac" not in matrices
    
    # Check matrix shape
    assert matrices["braycurtis"].shape == (3, 3)
    assert np.allclose(np.diag(matrices["braycurtis"].to_data_frame().values), 0.0)