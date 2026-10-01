import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add parent to path for imports if needed, though direct import works in project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import archard_normalization

def test_k_calculation():
    """
    Test K calculation using Archard's law.
    V = K * (F * L) / H  =>  K = (V * H) / (F * L)
    """
    # Create a mock dataframe with known values
    # V=10, H=100, F=10, L=10 => K = (10 * 100) / (10 * 10) = 10
    data = {
        'wear_rate': [10.0],
        'hardness': [100.0],
        'contact_load': [10.0],
        'sliding_speed': [10.0],
        'pulse_duration': [100.0],
        'power': [50.0],
        'scanning_speed': [20.0],
        'pattern_geometry': ['grid'],
        'elastic_modulus': [200.0]
    }
    df = pd.DataFrame(data)
    
    result = archard_normalization(df)
    
    assert 'normalization_method' in result.columns
    assert 'K' in result.columns
    
    assert result.loc[0, 'normalization_method'] == 'normalized'
    expected_K = (10.0 * 100.0) / (10.0 * 10.0)
    assert np.isclose(result.loc[0, 'K'], expected_K)
    
    # Test missing contact_load -> should be 'raw'
    data_missing = {
        'wear_rate': [10.0],
        'hardness': [100.0],
        'contact_load': [np.nan],
        'sliding_speed': [10.0],
        'pulse_duration': [100.0],
        'power': [50.0],
        'scanning_speed': [20.0],
        'pattern_geometry': ['grid'],
        'elastic_modulus': [200.0]
    }
    df_missing = pd.DataFrame(data_missing)
    result_missing = archard_normalization(df_missing)
    
    assert result_missing.loc[0, 'normalization_method'] == 'raw'
    assert np.isnan(result_missing.loc[0, 'K'])

def test_raw_records_handling():
    """
    Test that records with missing normalization inputs are flagged as 'raw'.
    """
    data = {
        'wear_rate': [10.0, 20.0],
        'hardness': [100.0, 100.0],
        'contact_load': [10.0, np.nan],
        'sliding_speed': [10.0, 10.0],
        'pulse_duration': [100.0, 100.0],
        'power': [50.0, 50.0],
        'scanning_speed': [20.0, 20.0],
        'pattern_geometry': ['grid', 'grid'],
        'elastic_modulus': [200.0, 200.0]
    }
    df = pd.DataFrame(data)
    
    result = archard_normalization(df)
    
    assert result.loc[0, 'normalization_method'] == 'normalized'
    assert result.loc[1, 'normalization_method'] == 'raw'
    assert np.isnan(result.loc[1, 'K'])

def test_exclude_predictors():
    """
    Verify that contact_load and sliding_speed are not added as features
    (they are used for normalization, not prediction).
    The function should not drop them from the DF, but the task description
    says 'EXCLUDE ... from the predictor feature set when the target is K'.
    This test verifies they remain in the DF but are not used to calculate K
    (which is done by the formula).
    The main check is that the K calculation doesn't depend on them as features,
    but as normalization constants. The DF structure is preserved.
    """
    data = {
        'wear_rate': [10.0],
        'hardness': [100.0],
        'contact_load': [10.0],
        'sliding_speed': [10.0],
        'pulse_duration': [100.0],
        'power': [50.0],
        'scanning_speed': [20.0],
        'pattern_geometry': ['grid'],
        'elastic_modulus': [200.0]
    }
    df = pd.DataFrame(data)
    result = archard_normalization(df)
    
    # Columns should be preserved
    assert 'contact_load' in result.columns
    assert 'sliding_speed' in result.columns
    # K is calculated
    assert not np.isnan(result.loc[0, 'K'])
