"""
Unit tests for preprocessing module, specifically interaction feature generation.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocessing import generate_interaction_features

def test_generate_interaction_features_basic():
    """Test that interaction features are created correctly."""
    data = {
        'Temperature': [100.0, 200.0, 300.0],
        'Mg': [1.0, 2.0, 3.0],
        'Si': [0.5, 1.0, 1.5],
        'GrainSize': [10.0, 20.0, 30.0]
    }
    df = pd.DataFrame(data)
    
    result = generate_interaction_features(df)
    
    # Check columns exist
    assert 'Temperature_Mg' in result.columns
    assert 'Temperature_Si' in result.columns
    
    # Check values
    assert result['Temperature_Mg'].iloc[0] == 100.0 * 1.0
    assert result['Temperature_Mg'].iloc[1] == 200.0 * 2.0
    assert result['Temperature_Si'].iloc[0] == 100.0 * 0.5

def test_generate_interaction_features_missing_temp():
    """Test that an error is raised if Temperature column is missing."""
    data = {
        'Mg': [1.0, 2.0],
        'Si': [0.5, 1.0],
        'GrainSize': [10.0, 20.0]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Temperature column not found"):
        generate_interaction_features(df)

def test_generate_interaction_features_no_composition():
    """Test that no interactions are created if no composition columns exist."""
    data = {
        'Temperature': [100.0, 200.0],
        'GrainSize': [10.0, 20.0]
    }
    df = pd.DataFrame(data)
    
    result = generate_interaction_features(df)
    
    # Should not create any new columns
    assert 'Temperature_Mg' not in result.columns
    assert len(result.columns) == 2

def test_generate_interaction_features_verification():
    """Test that verification step confirms columns exist."""
    data = {
        'Temperature': [100.0],
        'Mg': [1.0],
        'GrainSize': [10.0]
    }
    df = pd.DataFrame(data)
    
    result = generate_interaction_features(df)
    
    # Verify the column is present
    assert 'Temperature_Mg' in result.columns
    # Verify it's not NaN (if input wasn't NaN)
    assert not pd.isna(result['Temperature_Mg'].iloc[0])
