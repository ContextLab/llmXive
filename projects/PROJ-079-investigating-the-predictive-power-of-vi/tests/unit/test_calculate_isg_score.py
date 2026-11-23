"""
Unit tests for src.preprocess.calculate_isg_score
"""

import os
import pandas as pd
import numpy as np
import pytest

from src.preprocess import calculate_isg_score

def test_calculate_isg_score_empty_gene_list(tmp_path):
    """Providing an empty ISG gene list must raise a RuntimeError."""
    # Create a minimal normalized_counts DataFrame
    df = pd.DataFrame(
        np.random.rand(3, 2),
        index=["gene1", "gene2", "gene3"],
        columns=["sampleA", "sampleB"],
    )
    with pytest.raises(RuntimeError, match="ISG gene set is empty"):
        calculate_isg_score(df, [])

def test_calculate_isg_score_success(tmp_path, monkeypatch):
    """Valid input should produce a Series and write the CSV file."""
    # Build a deterministic normalized_counts DataFrame
    data = {
        "sample1": [1.0, 2.0, 3.0],
        "sample2": [2.0, 3.0, 4.0],
        "sample3": [3.0, 4.0, 5.0],
    }
    df = pd.DataFrame(data, index=["geneA", "geneB", "geneC"])

    # Use all genes as ISG set
    isg_genes = ["geneA", "geneB", "geneC"]

    # Run the function
    scores = calculate_isg_score(df, isg_genes)

    # Verify return type and length
    assert isinstance(scores, pd.Series)
    assert scores.shape[0] == df.shape[1]  # one score per sample
    assert list(scores.index) == ["sample1", "sample2", "sample3"]

    # Verify that the output CSV was created
    output_path = os.path.join("data", "processed", "isg_scores.csv")
    assert os.path.exists(output_path)

    # Load the CSV and compare
    loaded = pd.read_csv(output_path, index_col=0)
    pd.testing.assert_frame_equal(loaded, scores.to_frame())

# Ensure the test does not interfere with the real project data directory
# by monkeypatching the llmxive toolkit paths.data function if needed.
# In this environment the default paths point inside the repository,
# which is acceptable for the test.