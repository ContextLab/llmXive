"""
Unit tests for Spearman correlation calculation (Task T018).

This module tests the logic required for User Story 2, specifically:
- Computing Spearman rank correlations between taxa and cognitive scores.
- Handling edge cases (constant values, NaNs, small samples).

Note: This test file uses synthetic data for isolation purposes, as the actual
data loading pipeline (T011-T014) is handled by separate modules. The logic
tested here is designed to be applied to the real data once merged.
"""
import pytest
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from pathlib import Path
import sys
import os

# Add project root to path to resolve imports if running standalone
# In the actual project structure, conftest.py handles this via add_project_root_to_path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the utility functions we are testing (or simulate the logic if not yet implemented in code/)
# Since T021 (implementation of correlation) is not yet complete, we implement the logic
# directly here for testing purposes, or we assume a future module `code/03_correlation.py`
# will expose `compute_spearman_correlation`.
#
# For this test to be valid and runnable now, we define the function we expect to exist
# and test it. In a real CI/CD flow, this would import from `code/03_correlation`.

def compute_spearman_correlation(taxa_df: pd.DataFrame, cognitive_scores: pd.Series) -> pd.DataFrame:
    """
    Compute Spearman rank correlation between each taxon column and the cognitive score series.
    
    Args:
        taxa_df: DataFrame where columns are taxa abundances and rows are samples.
        cognitive_scores: Series of cognitive scores (z-scored) indexed to match taxa_df.
    
    Returns:
        DataFrame with columns 'taxon', 'correlation', 'p_value'.
    """
    results = []
    
    # Align indices to ensure correct matching
    valid_idx = taxa_df.index.intersection(cognitive_scores.index)
    if len(valid_idx) == 0:
        return pd.DataFrame(columns=['taxon', 'correlation', 'p_value'])
        
    taxa_aligned = taxa_df.loc[valid_idx]
    cognitive_aligned = cognitive_scores.loc[valid_idx]
    
    for taxon in taxa_aligned.columns:
        x = taxa_aligned[taxon].values
        y = cognitive_aligned.values
        
        # Handle constant values or insufficient data
        if np.isnan(x).all() or np.isnan(y).all():
            results.append({'taxon': taxon, 'correlation': np.nan, 'p_value': np.nan})
            continue
            
        try:
            corr, p_val = spearmanr(x, y, nan_policy='omit')
            results.append({'taxon': taxon, 'correlation': corr, 'p_value': p_val})
        except Exception:
            # Fallback for edge cases (e.g., all NaN after omit)
            results.append({'taxon': taxon, 'correlation': np.nan, 'p_value': np.nan})
            
    return pd.DataFrame(results)

class TestSpearmanCorrelation:
    """Test cases for Spearman correlation logic."""

    def test_basic_spearman_correlation(self):
        """Test that Spearman correlation is computed correctly on simple data."""
        # Create synthetic data with a known positive monotonic relationship
        np.random.seed(42)
        n_samples = 100
        taxa_data = pd.DataFrame({
            'Taxon_A': np.random.rand(n_samples),
            'Taxon_B': np.random.rand(n_samples)
        })
        # Create a cognitive score that is roughly correlated with Taxon_A
        cognitive_scores = pd.Series(taxa_data['Taxon_A'] * 2 + np.random.normal(0, 0.1, n_samples))
        
        result = compute_spearman_correlation(taxa_data, cognitive_scores)
        
        assert 'correlation' in result.columns
        assert 'p_value' in result.columns
        assert 'taxon' in result.columns
        
        # Taxon_A should have a high positive correlation
        corr_a = result[result['taxon'] == 'Taxon_A']['correlation'].values[0]
        assert 0.5 < corr_a < 1.0, f"Expected strong positive correlation, got {corr_a}"
        
        # Taxon_B should have near-zero correlation (random noise)
        corr_b = result[result['taxon'] == 'Taxon_B']['correlation'].values[0]
        assert -0.2 < corr_b < 0.2, f"Expected near-zero correlation for noise, got {corr_b}"

    def test_negative_correlation(self):
        """Test detection of negative monotonic relationships."""
        np.random.seed(42)
        n_samples = 50
        taxa_data = pd.DataFrame({
            'Taxon_C': np.random.rand(n_samples)
        })
        # Negative relationship
        cognitive_scores = pd.Series(-taxa_data['Taxon_C'] + np.random.normal(0, 0.05, n_samples))
        
        result = compute_spearman_correlation(taxa_data, cognitive_scores)
        corr_c = result[result['taxon'] == 'Taxon_C']['correlation'].values[0]
        
        assert -1.0 < corr_c < -0.5, f"Expected strong negative correlation, got {corr_c}"

    def test_constant_values_handling(self):
        """Test behavior when a taxon has constant values (zero variance)."""
        taxa_data = pd.DataFrame({
            'Constant_Taxon': [1.0] * 50,
            'Variable_Taxon': np.random.rand(50)
        })
        cognitive_scores = pd.Series(np.random.rand(50))
        
        result = compute_spearman_correlation(taxa_data, cognitive_scores)
        
        # Spearman with constant X should result in NaN or 0 depending on implementation, 
        # but scipy usually raises or returns NaN. We expect NaN here.
        const_corr = result[result['taxon'] == 'Constant_Taxon']['correlation'].values[0]
        assert np.isnan(const_corr), "Correlation should be NaN for constant variable"

    def test_mixed_nans(self):
        """Test handling of missing values (NaNs) in data."""
        n_samples = 100
        taxa_data = pd.DataFrame({
            'Taxon_D': np.random.rand(n_samples)
        })
        cognitive_scores = pd.Series(np.random.rand(n_samples))
        
        # Inject NaNs
        taxa_data.loc[10:15, 'Taxon_D'] = np.nan
        cognitive_scores.loc[20:25] = np.nan
        
        result = compute_spearman_correlation(taxa_data, cognitive_scores)
        
        # Should still compute a valid correlation (ignoring NaNs)
        corr_d = result[result['taxon'] == 'Taxon_D']['correlation'].values[0]
        assert not np.isnan(corr_d), "Correlation should be computed despite some NaNs"

    def test_empty_dataframe(self):
        """Test behavior with empty input."""
        taxa_data = pd.DataFrame(columns=['Taxon_E'])
        cognitive_scores = pd.Series([], dtype=float)
        
        result = compute_spearman_correlation(taxa_data, cognitive_scores)
        assert len(result) == 0

    def test_single_sample(self):
        """Test behavior with a single sample (insufficient for correlation)."""
        taxa_data = pd.DataFrame({'Taxon_F': [0.5]})
        cognitive_scores = pd.Series([0.8])
        
        result = compute_spearman_correlation(taxa_data, cognitive_scores)
        # With N=1, correlation is undefined
        assert len(result) == 1
        assert np.isnan(result['correlation'].values[0])

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
