import pytest
import pandas as pd
import numpy as np
from code.imbalance import calculate_gini, calculate_target_imbalance_score, calculate_compositional_imbalance_score, identify_target_columns
from unittest.mock import patch, MagicMock

def test_calculate_gini_positive():
    # Perfect equality -> Gini = 0
    data = pd.Series([10, 10, 10, 10])
    assert calculate_gini(data) == 0.0

def test_calculate_gini_inequality():
    # High inequality -> Gini > 0
    data = pd.Series([1, 1, 1, 100])
    gini = calculate_gini(data)
    assert 0 < gini <= 1.0

def test_calculate_gini_negative_values():
    # Should handle negative values via absolute transformation
    data = pd.Series([-10, -10, -10, -10])
    assert calculate_gini(data) == 0.0
    
    data_inequal = pd.Series([-1, -1, -1, -100])
    gini = calculate_gini(data_inequal)
    assert 0 < gini <= 1.0

def test_identify_target_columns():
    # Create a mock dataframe with known targets
    data = {
        'magpie_mean_atomic_number': [10.0, 20.0],
        'formation_energy': [-1.0, -2.0],
        'band_gap': [0.5, 1.0],
        'material_id': ['id1', 'id2']
    }
    df = pd.DataFrame(data)
    
    targets = identify_target_columns(df)
    assert 'formation_energy' in targets
    assert 'band_gap' in targets
    assert 'magpie_mean_atomic_number' not in targets

def test_calculate_target_imbalance_score_skip_small():
    # Create a dataframe with < 100 samples
    data = {
        'magpie_mean_atomic_number': [1.0] * 50,
        'formation_energy': [-1.0] * 50
    }
    df = pd.DataFrame(data)
    
    score = calculate_target_imbalance_score(df, 'formation_energy')
    assert score is None

def test_calculate_target_imbalance_score_valid():
    # Create a dataframe with >= 100 samples
    n = 100
    data = {
        'magpie_mean_atomic_number': [1.0] * n,
        'formation_energy': list(range(n))
    }
    df = pd.DataFrame(data)
    
    score = calculate_target_imbalance_score(df, 'formation_energy')
    assert score is not None
    assert 0 <= score <= 1.0

def test_calculate_compositional_imbalance_score():
    # Create a dataframe with enough samples for K-Means
    n = 200
    k = 50
    np.random.seed(42)
    features = {
        f'feat_{i}': np.random.rand(n) for i in range(10)
    }
    df = pd.DataFrame(features)
    
    score = calculate_compositional_imbalance_score(df, list(features.keys()))
    assert score is not None
    assert 0 <= score <= 1.0
