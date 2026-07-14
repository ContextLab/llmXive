"""
Unit tests for feature preparation in US2.
"""
import pytest
import pandas as pd
import numpy as np
from src.models.fit import map_eco_to_family, prepare_features_for_modeling

def test_map_eco_to_family_valid_codes():
    """Test mapping of valid ECO codes to families."""
    # King's Pawn / Sicilian
    assert map_eco_to_family('B12') == 'Caro-Kann'
    assert map_eco_to_family('B20') == 'Sicilian'
    assert map_eco_to_family('B90') == 'Sicilian'
    
    # Queen's Pawn / Queen's Gambit
    assert map_eco_to_family('D06') == 'Queen Gambit'
    assert map_eco_to_family('D10') == 'Queen Gambit'
    assert map_eco_to_family('D45') == 'Queen Gambit'
    
    # Indian Defenses
    assert map_eco_to_family('E12') == 'Indian'
    assert map_eco_to_family('E60') == 'Indian'
    
    # English Opening
    assert map_eco_to_family('A10') == 'English'
    assert map_eco_to_family('A30') == 'English'
    
    # Irregular openings
    assert map_eco_to_family('A00') == 'Irregular'

def test_map_eco_to_family_invalid_codes():
    """Test handling of invalid ECO codes."""
    assert map_eco_to_family('invalid') == 'Unknown'
    assert map_eco_to_family('Z99') == 'Unknown'
    assert map_eco_to_family('') == 'Unknown'
    assert map_eco_to_family(None) == 'Unknown'

def test_prepare_features_for_modeling_basic():
    """Test basic feature preparation."""
    # Create sample data
    df = pd.DataFrame({
        'game_id': ['g1', 'g2', 'g3'],
        'eco_code': ['B12', 'D06', 'E12'],
        'white_rating': [1500, 1800, 2000],
        'black_rating': [1550, 1750, 1950],
        'avg_move_time_white': [15.5, 20.3, 18.7],
        'avg_move_time_black': [16.2, 19.8, 19.1],
        'material_imbalance_move5': [0, 1, -1],
        'outcome_deviation': [0.1, -0.05, 0.2]
    })
    
    X, y, metadata = prepare_features_for_modeling(df)
    
    # Check output types
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert isinstance(metadata, dict)
    
    # Check shapes
    assert X.shape[0] == 3
    assert y.shape[0] == 3
    assert 'opening_family' in metadata['feature_columns'] or any('opening_' in col for col in metadata['feature_columns'])
    
    # Check metadata
    assert metadata['original_shape'] == (3, 8)
    assert metadata['n_samples'] == 3
    assert metadata['target_column'] == 'outcome_deviation'

def test_prepare_features_for_modeling_missing_values():
    """Test handling of missing values in features."""
    df = pd.DataFrame({
        'game_id': ['g1', 'g2', 'g3'],
        'eco_code': ['B12', 'D06', 'E12'],
        'white_rating': [1500, np.nan, 2000],
        'black_rating': [1550, 1750, 1950],
        'avg_move_time_white': [15.5, 20.3, np.nan],
        'avg_move_time_black': [16.2, 19.8, 19.1],
        'material_imbalance_move5': [0, 1, -1],
        'outcome_deviation': [0.1, -0.05, 0.2]
    })
    
    # Should not raise an error
    X, y, metadata = prepare_features_for_modeling(df)
    
    # Check that no NaN values remain in X
    assert not X.isnull().any().any()

def test_prepare_features_for_modeling_target_column():
    """Test that the correct target column is extracted."""
    df = pd.DataFrame({
        'game_id': ['g1', 'g2', 'g3'],
        'eco_code': ['B12', 'D06', 'E12'],
        'white_rating': [1500, 1800, 2000],
        'black_rating': [1550, 1750, 1950],
        'avg_move_time_white': [15.5, 20.3, 18.7],
        'avg_move_time_black': [16.2, 19.8, 19.1],
        'material_imbalance_move5': [0, 1, -1],
        'outcome_deviation': [0.1, -0.05, 0.2]
    })
    
    X, y, metadata = prepare_features_for_modeling(df, target_col='outcome_deviation')
    
    # Check that y matches the expected values
    expected_y = pd.Series([0.1, -0.05, 0.2], name='outcome_deviation')
    pd.testing.assert_series_equal(y, expected_y)

def test_prepare_features_for_modeling_missing_target():
    """Test error when target column is missing."""
    df = pd.DataFrame({
        'game_id': ['g1', 'g2', 'g3'],
        'eco_code': ['B12', 'D06', 'E12'],
        'white_rating': [1500, 1800, 2000],
    })
    
    with pytest.raises(ValueError, match="Target column"):
        prepare_features_for_modeling(df, target_col='outcome_deviation')

def test_prepare_features_for_modeling_missing_features():
    """Test error when required feature columns are missing."""
    df = pd.DataFrame({
        'game_id': ['g1', 'g2', 'g3'],
        'eco_code': ['B12', 'D06', 'E12'],
    })
    
    with pytest.raises(ValueError, match="Missing required feature columns"):
        prepare_features_for_modeling(df)