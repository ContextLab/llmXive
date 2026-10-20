"""
Unit tests for the phylogenetic covariance matrix construction.
"""

import numpy as np
import pandas as pd
import pytest
from llmxive_toolkit import paths

from code.modeling.phylo_compute import main as phylo_main
from code.modeling.phylo import load_phylogeny, construct_covariance_matrix

def test_covariance_dimensions_match_aligned(tmp_path, monkeypatch):
    """
    Verify that the covariance matrix written by ``phylo_compute`` has
    dimensions equal to the number of species in ``aligned_matrix.csv``.
    """
    # Create a minimal aligned matrix with three species
    aligned_df = pd.DataFrame({
        "species": ["spA", "spB", "spC"],
        "feat1": [0, 1, 2],
        "feat2": [3, 4, 5],
    })
    aligned_path = paths.data("processed", "aligned_matrix.csv")
    aligned_path.parent.mkdir(parents=True, exist_ok=True)
    aligned_df.to_csv(aligned_path, index=False)

    # Create a simple Newick tree containing the same three taxa
    newick = "(spA:0.1,spB:0.2,(spC:0.3) );"
    tree_path = paths.data("raw", "phylogeny", "tree.newick")
    tree_path.parent.mkdir(parents=True, exist_ok=True)
    tree_path.write_text(newick)

    # Run the covariance construction script
    phylo_main()

    # Load the produced matrix
    cov_path = paths.data("processed", "phylo_covariance.npy")
    assert cov_path.exists()
    cov = np.load(cov_path)

    # Expect a 3x3 matrix
    assert cov.shape == (3, 3)

def test_load_phylogeny_missing_file():
    """A missing tree file should raise PhylogenyError."""
    with pytest.raises(Exception):
        load_phylogeny("nonexistent_path.tree")