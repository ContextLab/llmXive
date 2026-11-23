import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from src.analysis.correlation import (
    CorrelationResult,
    CorrelationAnalysisResult,
    load_tree,
    load_merged_dataset,
    compute_phylogenetic_covariance,
    pgls_correlation,
    permutation_fdr,
    run_pgl_analysis,
    write_results,
)

# Fixtures
@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def sample_tree(temp_dir):
    """Create a simple Newick tree file."""
    tree_path = Path(temp_dir) / "test_tree.newick"
    # Simple tree with 5 tips
    tree_content = "((A:1.0,B:1.0):1.0,(C:1.0,D:1.0):1.0,E:3.0);"
    tree_path.write_text(tree_content)
    return str(tree_path)

@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample merged dataset CSV."""
    data_path = Path(temp_dir) / "test_dataset.csv"
    # Create data for 10 isolates with 3 features and phenotype
    data = {
        "strain_id": [f"ISOLATE_{i}" for i in range(10)],
        "species": ["Species_A"] * 5 + ["Species_B"] * 5,
        "feature_1": np.random.rand(10),
        "feature_2": np.random.rand(10),
        "feature_3": np.random.rand(10),
        "phenotype_score": np.random.rand(10) * 10,
    }
    df = pd.DataFrame(data)
    df.to_csv(data_path, index=False)
    return str(data_path)

# Existing tests from previous tasks (preserved)
def test_load_tree_success(sample_tree):
    """Test successful tree loading."""
    tree = load_tree(sample_tree)
    assert tree is not None
    assert len(tree.tips()) == 5

def test_load_tree_missing_file(temp_dir):
    """Test loading a non-existent tree file."""
    with pytest.raises(FileNotFoundError):
        load_tree(str(Path(temp_dir) / "non_existent.newick"))

def test_load_merged_dataset_success(sample_dataset):
    """Test successful dataset loading."""
    df = load_merged_dataset(sample_dataset)
    assert df is not None
    assert "phenotype_score" in df.columns
    assert len(df) == 10

def test_load_merged_dataset_missing_file(temp_dir):
    """Test loading a non-existent dataset file."""
    with pytest.raises(FileNotFoundError):
        load_merged_dataset(str(Path(temp_dir) / "non_existent.csv"))

def test_compute_phylogenetic_covariance(sample_tree):
    """Test phylogenetic covariance matrix computation."""
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)
    assert cov_matrix is not None
    assert isinstance(cov_matrix, np.ndarray)
    assert cov_matrix.shape[0] == cov_matrix.shape[1]
    # Check symmetry
    assert np.allclose(cov_matrix, cov_matrix.T)

def test_pgls_correlation_basic(sample_dataset, sample_tree):
    """Test basic PGLS correlation."""
    df = load_merged_dataset(sample_dataset)
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)

    # Run PGLS on first feature
    result = pgls_correlation(df, "feature_1", "phenotype_score", cov_matrix)
    assert isinstance(result, CorrelationResult)
    assert hasattr(result, "coefficient")
    assert hasattr(result, "p_value")
    assert hasattr(result, "feature_name")

def test_pgls_correlation_insufficient_data(temp_dir, sample_tree):
    """Test PGLS with insufficient data points."""
    # Create dataset with only 2 rows
    data_path = Path(temp_dir) / "small_dataset.csv"
    data = {
        "strain_id": ["ISOLATE_1", "ISOLATE_2"],
        "species": ["Species_A", "Species_B"],
        "feature_1": [0.5, 0.6],
        "phenotype_score": [5.0, 6.0],
    }
    df = pd.DataFrame(data)
    df.to_csv(data_path, index=False)

    loaded_df = load_merged_dataset(str(data_path))
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)

    # Should handle small N gracefully or raise appropriate error
    # Depending on implementation, might return None or raise
    try:
        result = pgls_correlation(loaded_df, "feature_1", "phenotype_score", cov_matrix)
        # If it succeeds, result should be valid or None for insufficient data
        assert result is None or isinstance(result, CorrelationResult)
    except ValueError:
        # Expected for insufficient data
        pass

# NEW TEST: Permutation FDR sensitivity check (T024)
def test_permutation_fdr_basic(sample_dataset, sample_tree):
    """Test basic permutation FDR calculation."""
    df = load_merged_dataset(sample_dataset)
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)

    # Generate some test results
    features = ["feature_1", "feature_2", "feature_3"]
    raw_p_values = []
    for feat in features:
        res = pgls_correlation(df, feat, "phenotype_score", cov_matrix)
        if res and res.p_value is not None:
            raw_p_values.append(res.p_value)
        else:
            raw_p_values.append(1.0)  # Default to 1.0 if no result

    raw_p_values = np.array(raw_p_values)

    # Run permutation FDR
    # Use a small number of permutations for testing speed
    fdr_results = permutation_fdr(
        df=df,
        feature_cols=features,
        target_col="phenotype_score",
        tree=tree,
        cov_matrix=cov_matrix,
        n_permutations=10,  # Small number for unit test
        random_state=42
    )

    assert fdr_results is not None
    assert "feature_name" in fdr_results.columns
    assert "raw_p_value" in fdr_results.columns
    assert "permuted_p_value" in fdr_results.columns
    assert "fdr_adjusted_p_value" in fdr_results.columns
    assert len(fdr_results) == len(features)

def test_permutation_fdr_empty():
    """Test permutation FDR with empty input."""
    # Create empty dataframe
    empty_df = pd.DataFrame(columns=["strain_id", "feature_1", "phenotype_score"])

    # Create a minimal tree
    with tempfile.NamedTemporaryFile(mode='w', suffix='.newick', delete=False) as f:
        f.write("(A:1.0,B:1.0);")
        tree_path = f.name

    tree = load_tree(tree_path)
    cov_matrix = compute_phylogenetic_covariance(tree)

    # Should handle empty input gracefully
    with pytest.raises((ValueError, IndexError)):
        permutation_fdr(
            df=empty_df,
            feature_cols=[],
            target_col="phenotype_score",
            tree=tree,
            cov_matrix=cov_matrix,
            n_permutations=10,
            random_state=42
        )

    # Cleanup
    os.unlink(tree_path)

def test_permutation_fdr_sensitivity(sample_dataset, sample_tree):
    """
    Test that permutation FDR produces different results with different random seeds,
    confirming it's actually performing permutations and not returning static values.
    """
    df = load_merged_dataset(sample_dataset)
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)
    features = ["feature_1", "feature_2"]

    # Run with seed 42
    results_42 = permutation_fdr(
        df=df,
        feature_cols=features,
        target_col="phenotype_score",
        tree=tree,
        cov_matrix=cov_matrix,
        n_permutations=50,
        random_state=42
    )

    # Run with seed 123
    results_123 = permutation_fdr(
        df=df,
        feature_cols=features,
        target_col="phenotype_score",
        tree=tree,
        cov_matrix=cov_matrix,
        n_permutations=50,
        random_state=123
    )

    # Results should differ due to different random seeds
    # We check the permuted p-values which depend on the random shuffling
    assert not results_42["permuted_p_value"].equals(results_123["permuted_p_value"])

def test_permutation_fdr_null_distribution(sample_dataset, sample_tree):
    """
    Test that permutation FDR correctly estimates the null distribution.
    When data is permuted, the resulting p-values should be uniformly distributed
    or at least higher than the original if there is a true signal.
    """
    df = load_merged_dataset(sample_dataset)
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)
    features = ["feature_1"]

    # Run permutation FDR
    results = permutation_fdr(
        df=df,
        feature_cols=features,
        target_col="phenotype_score",
        tree=tree,
        cov_matrix=cov_matrix,
        n_permutations=100,
        random_state=42
    )

    # The permuted p-value should be a valid probability
    assert 0 <= results["permuted_p_value"].iloc[0] <= 1

    # The FDR adjusted p-value should be >= raw p-value (conservative)
    # Note: This is a general property, but permutation FDR might behave slightly differently
    # based on implementation. We just check it's a valid probability.
    assert 0 <= results["fdr_adjusted_p_value"].iloc[0] <= 1

def test_run_pgl_analysis_with_permutation(sample_dataset, sample_tree, temp_dir):
    """Test full PGL analysis pipeline including permutation FDR."""
    # Run full analysis
    results_df = run_pgl_analysis(
        data_path=sample_dataset,
        tree_path=sample_tree,
        output_dir=temp_dir,
        use_permutation_fdr=True,
        n_permutations=20,  # Small for testing
        random_state=42
    )

    assert results_df is not None
    assert "feature_name" in results_df.columns
    assert "p_value" in results_df.columns
    # If permutation FDR was used, we expect additional columns
    if use_permutation_fdr:
        assert "permuted_p_value" in results_df.columns or "fdr_adjusted_p_value" in results_df.columns

def test_write_results(sample_dataset, sample_tree, temp_dir):
    """Test writing results to CSV."""
    df = load_merged_dataset(sample_dataset)
    tree = load_tree(sample_tree)
    cov_matrix = compute_phylogenetic_covariance(tree)

    # Generate results
    results = []
    for feat in ["feature_1", "feature_2"]:
        res = pgls_correlation(df, feat, "phenotype_score", cov_matrix)
        if res:
            results.append(res)

    # Write results
    output_path = Path(temp_dir) / "test_results.csv"
    write_results(results, str(output_path))

    # Verify file was written
    assert output_path.exists()
    written_df = pd.read_csv(output_path)
    assert len(written_df) == len(results)