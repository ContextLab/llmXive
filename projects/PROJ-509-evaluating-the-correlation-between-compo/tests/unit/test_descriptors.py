import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from descriptors import calculate_weighted_mean_variance, get_elemental_properties_df

def test_calculate_weighted_mean_variance():
    """Test the mean and variance calculation logic."""
    # Create mock composition data
    compositions = ['H2O', 'NaCl', 'Fe2O3']
    
    # Mock elemental properties (electronegativity)
    elemental_data = {
        'element': ['H', 'O', 'Na', 'Cl', 'Fe'],
        'electronegativity': [2.20, 3.44, 0.93, 3.16, 1.83]
    }
    elemental_df = pd.DataFrame(elemental_data)
    
    # Expected calculations:
    # H2O: mean = (2*2.20 + 1*3.44) / 3 = 2.613, variance = weighted variance
    # NaCl: mean = (1*0.93 + 1*3.16) / 2 = 2.045
    # Fe2O3: mean = (2*1.83 + 3*3.44) / 5 = 2.796
    
    result = calculate_weighted_mean_variance(compositions, elemental_df, 'electronegativity')
    
    assert 'electronegativity_mean' in result.columns
    assert 'electronegativity_variance' in result.columns
    assert len(result) == len(compositions)
    
    # Check specific values (with tolerance for floating point)
    assert abs(result.iloc[0]['electronegativity_mean'] - 2.613) < 0.01
    assert abs(result.iloc[1]['electronegativity_mean'] - 2.045) < 0.01
    assert abs(result.iloc[2]['electronegativity_mean'] - 2.796) < 0.01

def test_get_elemental_properties_df():
    """Test loading of elemental properties."""
    elemental_df = get_elemental_properties_df()
    
    # Check required columns exist
    required_cols = ['element', 'electronegativity', 'atomic_radius', 
                    'valence_electrons', 'melting_point', 'ionization_energy']
    
    for col in required_cols:
        assert col in elemental_df.columns, f"Missing column: {col}"
    
    # Check no null values in key property columns
    assert elemental_df['electronegativity'].notna().all()
    assert elemental_df['atomic_radius'].notna().all()