import pytest
import pandas as pd
import numpy as np
from src.models.fit import map_eco_to_family, prepare_features_for_modeling, ECO_FAMILIES
import json
from pathlib import Path
import tempfile

def test_map_eco_to_family_valid_codes():
    assert map_eco_to_family('A00') == 'Open Games'
    assert map_eco_to_family('B12') == 'Sicilian Defense'
    assert map_eco_to_family('C50') == 'French/Caro-Kann'
    assert map_eco_to_family('D35') == "Queen's Gambit"
    assert map_eco_to_family('E60') == "King's Indian"
    assert map_eco_to_family('F00') == 'English'
    assert map_eco_to_family('G00') == 'Réti'
    assert map_eco_to_family('H00') == 'Other'

def test_map_eco_to_family_invalid_codes():
    assert map_eco_to_family('Z99') == 'Other'
    assert map_eco_to_family('') == 'Other'
    assert map_eco_to_family(None) == 'Other'

def test_prepare_features_for_modeling_basic():
    df = pd.DataFrame({
        'eco_code': ['A00', 'B00', 'C00'],
        'avg_move_time_white': [10.0, 20.0, 30.0],
        'avg_move_time_black': [10.0, 20.0, 30.0],
        'material_imbalance_move10': [0, 1, -1],
        'outcome_deviation': [0.1, -0.1, 0.2]
    })
    X, y = prepare_features_for_modeling(df)
    assert X.shape[0] == 3
    assert 'eco_Open Games' in X.columns
    assert 'eco_Sicilian Defense' in X.columns
    assert 'eco_French/Caro-Kann' in X.columns
    assert len(y) == 3

def test_prepare_features_for_modeling_missing_values():
    df = pd.DataFrame({
        'eco_code': ['A00', 'B00', 'C00'],
        'avg_move_time_white': [10.0, np.nan, 30.0],
        'avg_move_time_black': [10.0, 20.0, 30.0],
        'material_imbalance_move10': [0, 1, -1],
        'outcome_deviation': [0.1, -0.1, 0.2]
    })
    X, y = prepare_features_for_modeling(df)
    # NaN should be filled with 0
    assert not X.isnull().any().any()
    assert X.iloc[1]['avg_move_time_white'] == 0

def test_prepare_features_for_modeling_target_column():
    df = pd.DataFrame({
        'eco_code': ['A00'],
        'avg_move_time_white': [10.0],
        'avg_move_time_black': [10.0],
        'material_imbalance_move10': [0],
        'outcome_deviation': [0.5]
    })
    X, y = prepare_features_for_modeling(df)
    assert y.iloc[0] == 0.5

def test_prepare_features_for_modeling_missing_target():
    df = pd.DataFrame({
        'eco_code': ['A00'],
        'avg_move_time_white': [10.0],
        'avg_move_time_black': [10.0],
        'material_imbalance_move10': [0]
    })
    with pytest.raises(ValueError, match="Target column 'outcome_deviation' not found"):
        prepare_features_for_modeling(df)

def test_prepare_features_for_modeling_missing_features():
    df = pd.DataFrame({
        'eco_code': ['A00'],
        'avg_move_time_white': [10.0],
        'outcome_deviation': [0.5]
    })
    with pytest.raises(ValueError, match="Required feature column"):
        prepare_features_for_modeling(df)
