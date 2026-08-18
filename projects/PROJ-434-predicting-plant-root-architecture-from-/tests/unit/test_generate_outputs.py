import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingestion.generate_outputs import count_valid_observations, generate_exclusion_summary

def test_count_valid_observations():
    """Test counting valid observations per species."""
    data = {
        'species_name': ['A', 'A', 'A', 'B', 'B'],
        'soil_n': [10.0, 10.0, np.nan, 20.0, 20.0],
        'soil_p': [10.0, 10.0, 10.0, 20.0, 20.0],
        'soil_k': [100.0, 100.0, 100.0, 200.0, 200.0],
        'soil_ph': [6.0, 6.0, 6.0, 6.0, 6.0],
        'root_depth': [5.0, 5.0, 5.0, 10.0, 10.0],
        'root_density': [0.5, 0.5, 0.5, 1.0, 1.0]
    }
    df = pd.DataFrame(data)
    
    counts = count_valid_observations(df)
    
    # Species A has 2 valid (3rd row has NaN soil_n)
    # Species B has 2 valid
    assert counts['A'] == 2
    assert counts['B'] == 2

def test_count_valid_observations_plausibility():
    """Test that physically implausible values are excluded."""
    data = {
        'species_name': ['A', 'A', 'A'],
        'soil_n': [10.0, 10.0, 10.0],
        'soil_p': [10.0, 10.0, 10.0],
        'soil_k': [100.0, 100.0, 100.0],
        'soil_ph': [2.0, 6.0, 10.0], # 2.0 and 10.0 are out of range
        'root_depth': [5.0, 5.0, 5.0],
        'root_density': [0.5, 0.5, 0.5]
    }
    df = pd.DataFrame(data)
    
    counts = count_valid_observations(df)
    
    # Only the middle row (pH 6.0) is valid
    assert counts['A'] == 1

def test_generate_exclusion_summary():
    """Test generating exclusion summary."""
    data = {
        'species_name': ['A', 'A', 'A', 'B', 'B', 'B', 'B', 'B'],
        'soil_n': [10.0] * 8,
        'soil_p': [10.0] * 8,
        'soil_k': [100.0] * 8,
        'soil_ph': [6.0] * 8,
        'root_depth': [5.0] * 8,
        'root_density': [0.5] * 8
    }
    df = pd.DataFrame(data)
    
    # A has 3 valid, B has 5 valid
    counts = {'A': 3, 'B': 5}
    
    summary = generate_exclusion_summary(df, counts, min_observations=4)
    
    assert len(summary) == 1
    assert summary.iloc[0]['species_name'] == 'A'
    assert summary.iloc[0]['observation_count'] == 3
    assert summary.iloc[0]['reason'] == 'observation_count < 4'

def test_generate_exclusion_summary_empty():
    """Test summary generation with no excluded species."""
    data = {
        'species_name': ['A', 'A', 'A', 'A', 'A'],
        'soil_n': [10.0] * 5,
        'soil_p': [10.0] * 5,
        'soil_k': [100.0] * 5,
        'soil_ph': [6.0] * 5,
        'root_depth': [5.0] * 5,
        'root_density': [0.5] * 5
    }
    df = pd.DataFrame(data)
    
    counts = {'A': 5}
    
    summary = generate_exclusion_summary(df, counts, min_observations=4)
    
    assert len(summary) == 0
    assert list(summary.columns) == ['species_name', 'observation_count', 'reason']