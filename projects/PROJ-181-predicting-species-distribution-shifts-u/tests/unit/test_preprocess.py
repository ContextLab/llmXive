import pandas as pd
import numpy as np
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from preprocess import filter_breeding_season, remove_duplicates, spatial_thin, validate_training_data

def test_filter_breeding_season():
    data = {
        'species': ['A', 'A', 'A', 'B'],
        'eventDate': ['2020-05-15', '2020-01-15', '2020-07-20', '2020-06-01'],
        'decimalLatitude': [40.0, 40.0, 40.0, 40.0],
        'decimalLongitude': [-75.0, -75.0, -75.0, -75.0]
    }
    df = pd.DataFrame(data)
    result = filter_breeding_season(df)
    # May, July, June are in breeding season (4-9). Jan is not.
    assert len(result) == 3
    assert 'eventDate' in result.columns

def test_remove_duplicates():
    data = {
        'species': ['A', 'A', 'A', 'B'],
        'decimalLatitude': [40.0, 40.0, 41.0, 40.0],
        'decimalLongitude': [-75.0, -75.0, -75.0, -75.0]
    }
    df = pd.DataFrame(data)
    result = remove_duplicates(df)
    # First two are duplicates (A, 40, -75). Keep one.
    assert len(result) == 3

def test_spatial_thin():
    # Create points: A at 0,0 and 0.1,0 (approx 11km apart), A at 0, 0.001 (approx 0.1km)
    # Distance threshold is 10km.
    # 0,0 and 0.1,0 -> ~11km -> Keep both.
    # 0,0 and 0, 0.001 -> ~0.1km -> Remove the second one.
    data = {
        'species': ['A', 'A', 'A'],
        'decimalLatitude': [0.0, 0.1, 0.001],
        'decimalLongitude': [0.0, 0.0, 0.0]
    }
    df = pd.DataFrame(data)
    # Min distance 10km
    result = spatial_thin(df, min_dist_km=10.0)
    # Should keep at least one point per cluster, but logic depends on shuffle order.
    # With seed, it's deterministic.
    # Point 0: 0,0. Point 1: 0.1,0 (~11km). Point 2: 0.001,0 (~0.1km).
    # If 0 is kept, 2 is removed. 1 is kept. Result: 0, 1.
    # If 2 is kept (shuffled first), 0 is removed (dist 0.1). 1 is kept. Result: 2, 1.
    # In either case, count should be 2.
    assert len(result) == 2

def test_validate_training_data():
    data = {
        'species': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C'],
        'decimalLatitude': [0.0]*22,
        'decimalLongitude': [0.0]*22
    }
    df = pd.DataFrame(data)
    # A: 5, B: 5, C: 12. Threshold 10.
    result, invalid = validate_training_data(df)
    assert len(result) == 12
    assert 'C' in result['species'].values
    assert 'A' not in result['species'].values
    assert 'B' not in result['species'].values
    assert set(invalid) == {'A', 'B'}
