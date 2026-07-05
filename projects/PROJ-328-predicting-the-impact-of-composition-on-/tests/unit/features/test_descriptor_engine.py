"""
Unit tests for the DescriptorEngine.
"""
import numpy as np
import pandas as pd
import pytest
from code.features.descriptor_engine import DescriptorEngine

def test_descriptor_engine_computation():
    """Test that descriptors are computed without error."""
    # Create a simple composition dataframe
    data = {
        'Sn': [0.965, 0.99],
        'Ag': [0.03, 0.005],
        'Cu': [0.005, 0.005]
    }
    df = pd.DataFrame(data)
    
    engine = DescriptorEngine()
    descriptors = engine.compute_descriptors(df)
    
    # Check that descriptors are computed
    expected_cols = [
        'weighted_mean_atomic_mass',
        'electronegativity_variance',
        'atomic_radius_variance',
        'weighted_avg_melting_point',
        'vec'
    ]
    
    for col in expected_cols:
        assert col in descriptors.columns, f"Missing column: {col}"
    
    # Check shape
    assert descriptors.shape[0] == df.shape[0]

def test_descriptor_engine_missing_element():
    """Test behavior with unknown elements."""
    # Create a composition with an unknown element
    data = {
        'Sn': [0.5],
        'Unknown': [0.5]
    }
    df = pd.DataFrame(data)
    
    engine = DescriptorEngine()
    # Should not raise an error, but log a warning
    descriptors = engine.compute_descriptors(df)
    
    assert descriptors.shape[0] == 1
