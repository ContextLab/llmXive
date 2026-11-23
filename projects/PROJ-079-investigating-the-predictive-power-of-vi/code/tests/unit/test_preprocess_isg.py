import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.preprocess import calculate_isg_score, save_isg_scores, run_isg_score_pipeline
from src.config import DATA_PROCESSED_PATH

@pytest.fixture
def sample_counts_matrix():
    """
    Creates a sample normalized counts matrix with some ISG genes and others.
    """
    np.random.seed(42)
    n_samples = 50
    n_genes = 100
    
    # Create gene names
    genes = [f"GENE_{i}" for i in range(n_genes)]
    # Assume first 10 are ISG genes
    isg_genes = genes[:10]
    
    # Generate random data
    data = np.random.rand(n_samples, n_genes) * 10
    
    df = pd.DataFrame(data, columns=genes)
    df.index = [f"Sample_{i}" for i in range(n_samples)]
    
    return df, isg_genes

def test_calculate_isg_score_basic(sample_counts_matrix):
    """
    Test that calculate_isg_score returns a Series with correct length and index.
    """
    df, isg_genes = sample_counts_matrix
    scores = calculate_isg_score(df, isg_genes)
    
    assert isinstance(scores, pd.Series)
    assert len(scores) == len(df)
    assert scores.name == 'isg_score'
    assert list(scores.index) == list(df.index)

def test_calculate_isg_score_empty_isg_list(sample_counts_matrix):
    """
    Test that an empty ISG gene list raises a ValueError.
    """
    df, _ = sample_counts_matrix
    with pytest.raises(ValueError, match="ISG gene list is empty"):
        calculate_isg_score(df, [])

def test_calculate_isg_score_missing_genes(sample_counts_matrix):
    """
    Test that missing ISG genes raise a ValueError.
    """
    df, _ = sample_counts_matrix
    missing_genes = ["NON_EXISTENT_GENE_1", "NON_EXISTENT_GENE_2"]
    with pytest.raises(ValueError, match="Missing ISG genes"):
        calculate_isg_score(df, missing_genes)

def test_calculate_isg_score_partial_missing_genes(sample_counts_matrix):
    """
    Test that partial missing ISG genes raise a ValueError.
    """
    df, isg_genes = sample_counts_matrix
    # Replace one valid gene with a missing one
    bad_genes = isg_genes[:-1] + ["MISSING_GENE"]
    with pytest.raises(ValueError, match="Missing ISG genes"):
        calculate_isg_score(df, bad_genes)

def test_calculate_isg_score_with_nan(sample_counts_matrix):
    """
    Test that NaN values in the data are handled correctly (rows dropped).
    """
    df, isg_genes = sample_counts_matrix
    # Introduce NaNs
    df.loc["Sample_0", isg_genes[0]] = np.nan
    df.loc["Sample_1", isg_genes[1]] = np.nan
    df.loc["Sample_2", isg_genes] = np.nan # All ISG genes NaN for this row
    
    scores = calculate_isg_score(df, isg_genes)
    
    # Row with all NaN in ISG genes should be dropped
    assert "Sample_2" not in scores.index
    # Rows with some NaN should be dropped (current implementation drops any row with NaN)
    assert "Sample_0" not in scores.index
    assert "Sample_1" not in scores.index
    assert len(scores) < len(df)

def test_save_isg_scores(sample_counts_matrix):
    """
    Test that save_isg_scores writes a file with correct content.
    """
    df, isg_genes = sample_counts_matrix
    scores = calculate_isg_score(df, isg_genes)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_isg_scores.csv")
        save_isg_scores(scores, output_path)
        
        assert os.path.exists(output_path)
        loaded_df = pd.read_csv(output_path, index_col=0)
        
        assert list(loaded_df.index) == list(scores.index)
        assert np.allclose(loaded_df["isg_score"].values, scores.values)

def test_run_isg_score_pipeline(sample_counts_matrix):
    """
    Test the full pipeline function.
    """
    df, isg_genes = sample_counts_matrix
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "pipeline_scores.csv")
        scores = run_isg_score_pipeline(df, isg_genes, output_path)
        
        assert os.path.exists(output_path)
        assert isinstance(scores, pd.Series)
        assert scores.name == 'isg_score'
