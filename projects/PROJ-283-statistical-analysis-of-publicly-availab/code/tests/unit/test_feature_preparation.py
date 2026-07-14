"""
Unit tests for feature preparation logic in src/models/fit.py.
"""
import pytest
import pandas as pd
import numpy as np
from src.models.fit import collapse_eco_to_family, prepare_features_for_model

class TestECOCollapse:
    def test_sicilian_defense(self):
        assert collapse_eco_to_family('B20') == 'Sicilian Defense'
        assert collapse_eco_to_family('b12') == 'Sicilian Defense'
    
    def test_open_games(self):
        assert collapse_eco_to_family('C50') == 'Open Games'
        assert collapse_eco_to_family('B00') == 'Open Games'
    
    def test_queens_pawn(self):
        assert collapse_eco_to_family('D00') == 'Queen\'s Pawn Games'
    
    def test_indian_defenses(self):
        assert collapse_eco_to_family('E60') == 'Indian Defenses'
    
    def test_unknown(self):
        assert collapse_eco_to_family('Z99') == 'Unknown'
        assert collapse_eco_to_family('') == 'Unknown'
        assert collapse_eco_to_family(None) == 'Unknown'

class TestPrepareFeatures:
    @pytest.fixture
    def sample_data(self):
        return pd.DataFrame({
            'white_rating': [1500, 1600, 1700, 1800],
            'black_rating': [1500, 1600, 1700, 1800],
            'avg_move_time_white': [10.0, 12.0, 15.0, 20.0],
            'avg_move_time_black': [10.0, 12.0, 15.0, 20.0],
            'material_imbalance_move5': [0, 1, 0, 2],
            'eco_code': ['B20', 'C50', 'D00', 'E60'],
            'outcome_deviation': [0.1, -0.2, 0.05, -0.1]
        })

    def test_prepare_features_basic(self, sample_data):
        X, y = prepare_features_for_model(sample_data, collapse_eco=True)
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(y) == 4
        assert 'white_rating' in X.columns
        assert 'avg_move_time_white' in X.columns
        # Check that ECO family columns are created
        assert any('eco_family' in col for col in X.columns)

    def test_prepare_features_no_collapse(self, sample_data):
        X, y = prepare_features_for_model(sample_data, collapse_eco=False)
        assert 'eco_code' not in X.columns # Should be encoded
        assert any('eco_code' in col for col in X.columns)

    def test_missing_values_handling(self):
        data = pd.DataFrame({
            'white_rating': [1500, np.nan, 1700],
            'black_rating': [1500, 1600, 1700],
            'avg_move_time_white': [10.0, 12.0, 15.0],
            'avg_move_time_black': [10.0, 12.0, 15.0],
            'material_imbalance_move5': [0, 1, 0],
            'eco_code': ['B20', 'C50', 'D00'],
            'outcome_deviation': [0.1, 0.2, 0.3]
        })
        X, y = prepare_features_for_model(data, collapse_eco=True)
        # Should drop the row with NaN
        assert len(y) == 2

    def test_missing_columns(self, sample_data):
        # Remove a required column
        data = sample_data.drop(columns=['white_rating'])
        with pytest.raises(ValueError):
            prepare_features_for_model(data, collapse_eco=True)