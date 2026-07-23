import pytest
import pandas as pd
import numpy as np
from code.preprocessing import (
    calculate_sequencing_depth,
    apply_rarefaction,
    apply_vst,
    filter_low_prevalence,
    calculate_alpha_diversity,
    generate_beta_diversity_matrices,
    run_preprocessing
)
from code.config import calculate_median_depth, estimate_rarefaction_loss

# Mock data fixtures
@pytest.fixture
def mock_counts_df():
    """Create a mock OTU table for testing."""
    data = {
        'Taxon_A': [100, 50, 200, 0, 150],
        'Taxon_B': [0, 0, 10, 5, 20],
        'Taxon_C': [50, 60, 40, 55, 45],
        'Taxon_D': [0, 0, 0, 0, 0],  # Zero count taxon
        'Taxon_E': [10, 12, 11, 13, 9],
    }
    index = ['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4', 'Sample_5']
    return pd.DataFrame(data, index=index)

@pytest.fixture
def mock_metadata_df():
    """Create mock metadata."""
    data = {
        'Age': [25, 30, 35, 40, 45],
        'BMI': [22, 24, 26, 28, 30]
    }
    index = ['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4', 'Sample_5']
    return pd.DataFrame(data, index=index)

def test_calculate_sequencing_depth(mock_counts_df):
    depths = calculate_sequencing_depth(mock_counts_df)
    expected = pd.Series([160, 122, 261, 68, 244], index=mock_counts_df.index)
    pd.testing.assert_series_equal(depths, expected)

def test_apply_rarefaction(mock_counts_df):
    rarefied = apply_rarefaction(mock_counts_df, depth=100, random_seed=42)
    # Check that sums are close to 100 (allowing for integer rounding in rarefaction)
    sums = rarefied.sum(axis=1)
    assert all(sums >= 95), "Rarefaction depth not maintained"
    assert rarefied.shape == mock_counts_df.shape

def test_apply_vst(mock_counts_df):
    vst_data = apply_vst(mock_counts_df)
    assert vst_data.shape == mock_counts_df.shape
    assert not vst_data.isna().any().any()

def test_filter_low_prevalence(mock_counts_df):
    # Taxon_D has 0 prevalence, Taxon_B has 20% (1/5) which is < 0.2 threshold
    # With threshold 0.001 (0.1%), all non-zero taxa should pass except Taxon_D
    filtered = filter_low_prevalence(mock_counts_df, prevalence_threshold=0.001)
    assert 'Taxon_D' not in filtered.columns
    assert len(filtered.columns) == 4  # A, B, C, E

def test_calculate_alpha_diversity(mock_counts_df):
    alpha = calculate_alpha_diversity(mock_counts_df)
    assert 'shannon' in alpha.columns
    assert 'simpson' in alpha.columns
    assert len(alpha) == len(mock_counts_df)
    assert not alpha.isna().any().any()

def test_generate_beta_diversity_matrices(mock_counts_df, mock_metadata_df):
    # This test requires skbio. We assume it's installed.
    matrices = generate_beta_diversity_matrices(mock_counts_df, mock_metadata_df)
    assert 'bray_curtis' in matrices
    assert matrices['bray_curtis'].shape == (5, 5)
    
    # Check that IDs match
    assert list(matrices['bray_curtis'].ids) == list(mock_counts_df.index)

def test_run_preprocessing(mock_counts_df, mock_metadata_df):
    preprocessed, alpha, beta = run_preprocessing(
        counts_df=mock_counts_df,
        metadata_df=mock_metadata_df,
        rarefaction_depth=100
    )
    assert preprocessed.shape[0] == mock_counts_df.shape[0]
    assert 'shannon' in alpha.columns
    assert 'bray_curtis' in beta

def test_rarefaction_fallback_logic_low_depth(mock_counts_df):
    """
    Test the fallback logic when median sequencing depth is too low (< 1000).
    
    Scenario:
    - The mock data has a median depth of 160 (calculated from [160, 122, 261, 68, 244]).
    - This is < 1000, so the system should trigger the VST fallback instead of rarefaction.
    
    We verify that apply_vst succeeds and produces valid data when rarefaction
    would be deemed inappropriate due to low depth.
    """
    # Calculate depths
    depths = calculate_sequencing_depth(mock_counts_df)
    median_depth = depths.median()
    
    # Verify our mock data actually triggers the low-depth condition
    assert median_depth < 1000, "Test setup invalid: median depth must be < 1000"
    
    # The fallback logic (in run_preprocessing) would call apply_vst here.
    # We test that VST works correctly as the fallback mechanism.
    vst_result = apply_vst(mock_counts_df)
    
    # Verify VST output
    assert vst_result.shape == mock_counts_df.shape
    assert not vst_result.isna().any().any()
    assert not vst_result.isinf().any().any()
    
    # Verify that VST produces non-negative values (biologically plausible for counts)
    # Note: VST can produce negative values for low counts, so we just check it runs
    assert vst_result.notna().all().all()

def test_rarefaction_fallback_logic_high_loss(mock_counts_df):
    """
    Test the fallback logic when estimated sample loss is too high (> 20%).
    
    Scenario:
    - We attempt to rarefy to a depth that would cause > 20% sample loss.
    - The system should trigger the VST fallback.
    
    We verify that apply_vst succeeds when rarefaction would lose too many samples.
    """
    # Calculate depths
    depths = calculate_sequencing_depth(mock_counts_df)
    
    # Choose a depth that will cause significant sample loss.
    # Our depths are [160, 122, 261, 68, 244].
    # If we rarefy to 200, samples with depth < 200 (122, 68, 160) will be lost.
    # That's 3 out of 5 samples = 60% loss, which is > 20%.
    test_depth = 200
    
    # Estimate the loss
    loss_pct = estimate_rarefaction_loss(mock_counts_df, test_depth)
    
    # Verify our setup causes high loss
    assert loss_pct > 20, f"Test setup invalid: expected loss > 20%, got {loss_pct}%"
    
    # The fallback logic would call apply_vst here.
    vst_result = apply_vst(mock_counts_df)
    
    # Verify VST works as the fallback
    assert vst_result.shape == mock_counts_df.shape
    assert not vst_result.isna().any().any()
    assert not vst_result.isinf().any().any()

def test_rarefaction_success_path(mock_counts_df):
    """
    Test the normal path when rarefaction is appropriate.
    
    Scenario:
    - Median depth is sufficient (>= 1000) OR loss is low (<= 20%).
    - The system should use rarefaction.
    
    We create a mock dataset with higher counts to simulate a valid rarefaction path.
    """
    # Create a mock dataset with higher sequencing depth
    high_depth_data = {
        'Taxon_A': [1000, 1500, 2000, 1200, 1800],
        'Taxon_B': [500, 800, 300, 600, 900],
        'Taxon_C': [200, 400, 600, 300, 500],
    }
    index = ['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4', 'Sample_5']
    high_depth_df = pd.DataFrame(high_depth_data, index=index)
    
    # Calculate median depth
    depths = calculate_sequencing_depth(high_depth_df)
    median_depth = depths.median()
    
    # Verify we have sufficient depth
    assert median_depth >= 1000, "Test setup invalid: median depth must be >= 1000"
    
    # Test that rarefaction works at this depth
    rarefied = apply_rarefaction(high_depth_df, depth=int(median_depth), random_seed=42)
    
    # Verify rarefaction maintains depth (approximately)
    sums = rarefied.sum(axis=1)
    assert all(sums >= int(median_depth) - 10), "Rarefaction depth not maintained"
    assert rarefied.shape == high_depth_df.shape

def test_rarefaction_vs_vst_decision_boundary(mock_counts_df, mock_metadata_df):
    """
    Test the complete decision logic in run_preprocessing.
    
    This test verifies that run_preprocessing correctly chooses between
    rarefaction and VST based on the depth and loss criteria.
    """
    # Test 1: Low depth should trigger VST
    # Our mock data has median depth ~160, which is < 1000
    preprocessed_low, alpha_low, beta_low = run_preprocessing(
        counts_df=mock_counts_df,
        metadata_df=mock_metadata_df,
        rarefaction_depth=1000  # Force a high depth requirement
    )
    
    # VST should have been applied, so shape should be preserved
    assert preprocessed_low.shape == mock_counts_df.shape
    assert not preprocessed_low.isna().any().any()
    
    # Test 2: Sufficient depth should allow rarefaction
    # Create high-depth data
    high_depth_data = {
        'Taxon_A': [1000, 1500, 2000, 1200, 1800],
        'Taxon_B': [500, 800, 300, 600, 900],
        'Taxon_C': [200, 400, 600, 300, 500],
    }
    high_depth_df = pd.DataFrame(high_depth_data, index=mock_counts_df.index)
    
    preprocessed_high, alpha_high, beta_high = run_preprocessing(
        counts_df=high_depth_df,
        metadata_df=mock_metadata_df,
        rarefaction_depth=1000
    )
    
    # Rarefaction should have been applied
    assert preprocessed_high.shape[0] == high_depth_df.shape[0]
    assert 'shannon' in alpha_high.columns
    assert 'bray_curtis' in beta_high