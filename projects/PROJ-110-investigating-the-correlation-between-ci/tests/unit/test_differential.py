import pytest
import pandas as pd
import numpy as np
from analysis.differential import compute_effect_sizes

def test_cohens_d_calculation():
    """Test that Cohen's d is calculated correctly for known values."""
    # Create synthetic data where we know the effect size
    # Group 1 (MetS): mean=10, std=2, n=20
    # Group 2 (Control): mean=8, std=2, n=20
    # Expected Cohen's d = (10 - 8) / 2 = 1.0
    
    np.random.seed(42)
    met_s_data = np.random.normal(loc=10, scale=2, size=20)
    control_data = np.random.normal(loc=8, scale=2, size=20)
    
    expression_df = pd.DataFrame({
        'TEST_GENE': np.concatenate([met_s_data, control_data])
    }, index=[f'S{i}' for i in range(20)] + [f'C{i}' for i in range(20)])
    
    phenotype_df = pd.DataFrame({
        'MetS_status': ['MetS'] * 20 + ['Control'] * 20
    }, index=expression_df.index)
    
    result = compute_effect_sizes(expression_df, phenotype_df, ['TEST_GENE'])
    
    assert len(result) == 1
    assert result['gene'].iloc[0] == 'TEST_GENE'
    # Allow some tolerance due to random sampling
    assert 0.8 < result['cohens_d'].iloc[0] < 1.2, f"Expected ~1.0, got {result['cohens_d'].iloc[0]}"
    assert result['n_met_s'].iloc[0] == 20
    assert result['n_control'].iloc[0] == 20

def test_effect_size_missing_gene():
    """Test that missing genes are handled gracefully."""
    expression_df = pd.DataFrame({
        'EXISTING_GENE': [1, 2, 3, 4, 5, 6]
    }, index=['S0', 'S1', 'S2', 'C0', 'C1', 'C2'])
    
    phenotype_df = pd.DataFrame({
        'MetS_status': ['MetS', 'MetS', 'MetS', 'Control', 'Control', 'Control']
    }, index=expression_df.index)
    
    result = compute_effect_sizes(expression_df, phenotype_df, ['MISSING_GENE'])
    
    assert len(result) == 0  # Should return empty DataFrame for missing gene

def test_effect_size_insufficient_samples():
    """Test that groups with <2 samples are excluded."""
    expression_df = pd.DataFrame({
        'TEST_GENE': [1, 2, 3]
    }, index=['S0', 'S1', 'C0'])
    
    phenotype_df = pd.DataFrame({
        'MetS_status': ['MetS', 'MetS', 'Control']
    }, index=expression_df.index)
    
    result = compute_effect_sizes(expression_df, phenotype_df, ['TEST_GENE'])
    
    assert len(result) == 0  # Should return empty DataFrame due to insufficient control samples

def test_effect_size_zero_variance():
    """Test Cohen's d when pooled std is zero."""
    expression_df = pd.DataFrame({
        'TEST_GENE': [5, 5, 5, 5, 5, 5]
    }, index=['S0', 'S1', 'S2', 'C0', 'C1', 'C2'])
    
    phenotype_df = pd.DataFrame({
        'MetS_status': ['MetS', 'MetS', 'MetS', 'Control', 'Control', 'Control']
    }, index=expression_df.index)
    
    result = compute_effect_sizes(expression_df, phenotype_df, ['TEST_GENE'])
    
    assert len(result) == 1
    assert result['cohens_d'].iloc[0] == 0.0
    assert result['n_met_s'].iloc[0] == 3
    assert result['n_control'].iloc[0] == 3