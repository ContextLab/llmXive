import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path to import preprocess module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from preprocess import normalize_column_synonyms, impute_missing_values, normalize_features, create_feature_subsets

def test_median_imputation():
    """Verify median imputation with synthetic missing data."""
    data = {
        'laser_power': [100.0, 200.0, np.nan, 400.0],
        'scan_speed': [1000.0, np.nan, 3000.0, 4000.0]
    }
    df = pd.DataFrame(data)
    
    df_imputed = impute_missing_values(df)
    
    # Check no nulls
    assert df_imputed.isnull().sum().sum() == 0
    
    # Check median calculation
    # laser_power median of [100, 200, 400] is 200
    assert df_imputed['laser_power'].iloc[2] == 200.0
    # scan_speed median of [1000, 3000, 4000] is 3000
    assert df_imputed['scan_speed'].iloc[1] == 3000.0

def test_normalization():
    """Verify normalization scaling to [0, 1] range."""
    data = {
        'laser_power': [100.0, 200.0, 300.0],
        'scan_speed': [1000.0, 2000.0, 4000.0]
    }
    df = pd.DataFrame(data)
    
    df_norm = normalize_features(df)
    
    # Check range
    assert df_norm['laser_power'].min() == 0.0
    assert df_norm['laser_power'].max() == 1.0
    assert df_norm['scan_speed'].min() == 0.0
    assert df_norm['scan_speed'].max() == 1.0
    
    # Check specific values
    # laser_power: (100-100)/(300-100)=0, (200-100)/200=0.5, (300-100)/200=1
    assert df_norm['laser_power'].iloc[0] == 0.0
    assert df_norm['laser_power'].iloc[1] == 0.5
    assert df_norm['laser_power'].iloc[2] == 1.0

def test_feature_subsets():
    """Verify creation of X_raw and X_derived subsets."""
    data = {
        'laser_power': [100.0],
        'scan_speed': [1000.0],
        'hatch_spacing': [0.1],
        'layer_thickness': [0.05],
        'energy_density': [1000.0],
        'porosity': [0.5]
    }
    df = pd.DataFrame(data)
    
    X_raw, X_derived = create_feature_subsets(df)
    
    assert list(X_raw.columns) == ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    assert list(X_derived.columns) == ['energy_density']
    assert 'porosity' not in X_raw.columns
    assert 'porosity' not in X_derived.columns
