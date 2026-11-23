import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.analysis import calculate_bivariate_correlations, check_significance

@pytest.fixture
def sample_data():
    """Create a mock dataframe for testing correlation logic."""
    np.random.seed(42)
    n = 100
    data = {
        'smiles': [f"mol_{i}" for i in range(n)],
        'logPapp': np.random.normal(0, 1, n),
        'bond_variance': np.random.normal(0, 1, n),
        'angle_variance': np.random.normal(0, 1, n),
        'dihedral_variance': np.random.normal(0, 1, n)
    }
    return pd.DataFrame(data)

def test_correlation_calculation(sample_data):
    """Test that correlations are calculated correctly for all descriptors."""
    results = calculate_bivariate_correlations(sample_data)
    
    # Check that we have results for all three descriptors
    assert len(results) == 3
    assert set(results['descriptor'].tolist()) == {'bond_variance', 'angle_variance', 'dihedral_variance'}
    
    # Check that correlation coefficients are within [-1, 1]
    for _, row in results.iterrows():
        assert -1 <= row['pearson_r'] <= 1
        assert -1 <= row['spearman_r'] <= 1
        
    # Check that p-values are within [0, 1]
    for _, row in results.iterrows():
        assert 0 <= row['pearson_p'] <= 1
        assert 0 <= row['spearman_p'] <= 1

def test_significance_check():
    """Test the significance check function."""
    assert check_significance(0.01) == True
    assert check_significance(0.049) == True
    assert check_significance(0.05) == False
    assert check_significance(0.1) == False
    
    # Test with custom alpha
    assert check_significance(0.01, alpha=0.001) == False

def test_missing_columns_handling():
    """Test that the function handles missing columns gracefully."""
    data = pd.DataFrame({
        'smiles': ['mol_1', 'mol_2'],
        'logPapp': [1.0, 2.0]
        # Missing descriptor columns
    })
    
    results = calculate_bivariate_correlations(data)
    
    # Should return an empty dataframe if no descriptors are found
    assert results.empty