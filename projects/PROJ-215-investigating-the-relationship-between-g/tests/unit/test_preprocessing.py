import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the function to test
from code.preprocessing import (
    calculate_sequencing_depth,
    estimate_rarefaction_loss,
    apply_rarefaction,
    apply_vst,
    filter_low_prevalence,
    calculate_alpha_diversity,
    generate_beta_diversity_matrices
)

@pytest.fixture
def sample_otu_table():
    """Create a small synthetic OTU table for testing."""
    data = {
        'Taxon_A': [10, 20, 30, 0],
        'Taxon_B': [5, 10, 15, 0],
        'Taxon_C': [2, 4, 6, 100]
    }
    index = ['Sample1', 'Sample2', 'Sample3', 'Sample4']
    return pd.DataFrame(data, index=index)

@pytest.fixture
def sample_otu_table_with_zeros():
    """Table with many zeros to test prevalence."""
    data = {
        'Taxon_X': [10, 0, 0, 0],
        'Taxon_Y': [5, 5, 5, 5],
        'Taxon_Z': [1, 0, 1, 0]
    }
    index = ['S1', 'S2', 'S3', 'S4']
    return pd.DataFrame(data, index=index)

def test_calculate_sequencing_depth(sample_otu_table):
    depth = calculate_sequencing_depth(sample_otu_table)
    # Sums: 17, 34, 51, 100. Median of [17, 34, 51, 100] is (34+51)/2 = 42.5
    expected = 42.5
    assert abs(depth - expected) < 1e-6

def test_estimate_rarefaction_loss(sample_otu_table):
    # Depth 42.5. Samples < 42.5: S1(17), S2(34). Count = 2. Total = 4. Loss = 50%
    loss = estimate_rarefaction_loss(sample_otu_table, 42.5)
    assert loss == 50.0

def test_apply_rarefaction(sample_otu_table):
    # Rarefy to 15. S1(17), S2(34), S3(51) pass. S4(100) passes? No, wait.
    # Sums: 17, 34, 51, 100.
    # If depth=15: All pass.
    # If depth=20: S1(17) fails. S2, S3, S4 pass.
    result = apply_rarefaction(sample_otu_table, 20)
    assert len(result) == 3
    assert 'Sample1' not in result.index
    assert 'Sample2' in result.index

def test_apply_vst(sample_otu_table):
    result = apply_vst(sample_otu_table)
    assert result.shape == sample_otu_table.shape
    assert not result.isna().any().any()

def test_filter_low_prevalence(sample_otu_table_with_zeros):
    # 4 samples.
    # Taxon_X: 1/4 = 0.25
    # Taxon_Y: 4/4 = 1.0
    # Taxon_Z: 2/4 = 0.5
    # Threshold 0.3: Keep X, Y, Z? No, X is 0.25 < 0.3. Keep Y, Z.
    result = filter_low_prevalence(sample_otu_table_with_zeros, threshold=0.3)
    assert len(result.columns) == 2
    assert 'Taxon_Y' in result.columns
    assert 'Taxon_Z' in result.columns
    assert 'Taxon_X' not in result.columns

def test_calculate_alpha_diversity(sample_otu_table):
    # Test that it returns a DataFrame with expected columns
    result = calculate_alpha_diversity(sample_otu_table)
    assert 'shannon' in result.columns
    assert 'simpson' in result.columns
    assert len(result) == len(sample_otu_table)

def test_generate_beta_diversity_matrices_no_tree(sample_otu_table):
    with tempfile.TemporaryDirectory() as tmpdir:
        results = generate_beta_diversity_matrices(sample_otu_table, tree=None, output_dir=tmpdir)
        assert 'bray_curtis' in results
        assert os.path.exists(results['bray_curtis'])
        assert 'weighted_unifrac' not in results
        assert 'unweighted_unifrac' not in results

        # Verify content
        data = np.load(results['bray_curtis'])
        assert 'distances' in data
        assert 'sample_ids' in data
        assert data['distances'].shape[0] > 0

def test_generate_beta_diversity_matrices_empty_table():
    empty_df = pd.DataFrame()
    with tempfile.TemporaryDirectory() as tmpdir:
        results = generate_beta_diversity_matrices(empty_df, tree=None, output_dir=tmpdir)
        assert results == {}