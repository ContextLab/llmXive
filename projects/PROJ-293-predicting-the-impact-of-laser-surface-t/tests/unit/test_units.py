import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if needed, though usually handled by runner
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import convert_units

def test_wear_rate_conversion():
    """
    Test T013b: convert_units logic.
    Verifies conversion of linear (mm) and mass (mg) wear rates to Volume (mm3).
    """
    
    # Test Case 1: Linear wear (mm) to Volume (mm3)
    # V = Area * depth. Assume geometry is area in mm2.
    df_linear = pd.DataFrame({
        'wear_rate': [1.0, 2.0, 0.5],
        'wear_rate_unit': ['mm', 'mm', 'mm'],
        'density': [7.8, 7.8, 7.8], # Not used for linear
        'geometry': [10.0, 20.0, 5.0] # Area in mm2
    })
    
    result_linear = convert_units(df_linear)
    
    # Expected: 1.0 * 10.0 = 10.0, 2.0 * 20.0 = 40.0, 0.5 * 5.0 = 2.5
    expected_linear = [10.0, 40.0, 2.5]
    
    assert list(result_linear['wear_rate']) == expected_linear
    assert all(result_linear['wear_rate_unit'] == 'mm3')
    assert 'wear_rate_unit' in result_linear.columns
    
    # Test Case 2: Mass wear (mg) to Volume (mm3)
    # V = mass / density. Assumption: density in g/cm3.
    # Formula derived: V (mm3) = mass_mg / density_g_cm3
    # Example: 100 mg, density 7.8 g/cm3 -> 100 / 7.8 = 12.82 mm3
    df_mass = pd.DataFrame({
        'wear_rate': [100.0, 78.0],
        'wear_rate_unit': ['mg', 'mg'],
        'density': [7.8, 7.8],
        'geometry': [0.0, 0.0] # Not used
    })
    
    result_mass = convert_units(df_mass)
    
    # 100 / 7.8 = 12.8205...
    # 78 / 7.8 = 10.0
    expected_mass_1 = 100.0 / 7.8
    expected_mass_2 = 78.0 / 7.8
    
    assert np.isclose(result_mass['wear_rate'].iloc[0], expected_mass_1)
    assert np.isclose(result_mass['wear_rate'].iloc[1], expected_mass_2)
    assert all(result_mass['wear_rate_unit'] == 'mm3')
    
    # Test Case 3: Ambiguous unit should raise ValueError
    df_ambig = pd.DataFrame({
        'wear_rate': [1.0],
        'wear_rate_unit': ['unknown_unit'],
        'density': [7.8],
        'geometry': [10.0]
    })
    
    with pytest.raises(ValueError, match="Ambiguous wear_rate_unit"):
        convert_units(df_ambig)
    
    # Test Case 4: Missing required columns should raise ValueError
    df_missing = pd.DataFrame({
        'wear_rate': [1.0],
        'wear_rate_unit': ['mm']
        # Missing density, geometry
    })
    
    with pytest.raises(ValueError, match="Missing required columns"):
        convert_units(df_missing)
    
    print("All unit conversion tests passed.")

if __name__ == "__main__":
    test_wear_rate_conversion()
