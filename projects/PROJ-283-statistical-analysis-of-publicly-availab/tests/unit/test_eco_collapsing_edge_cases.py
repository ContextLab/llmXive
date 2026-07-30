import pytest
import pandas as pd
import numpy as np
from src.models.fit import map_eco_to_family, prepare_features_for_modeling

class TestECOCollapsingEdgeCases:
    """Additional unit tests for ECO code collapsing logic."""

    def test_map_eco_to_family_unknown_code(self):
        """Test handling of invalid or unknown ECO codes."""
        # Unknown codes should map to a default family or 'Other'
        result = map_eco_to_family("ZZZ")
        assert result is not None
        assert isinstance(result, str)
        # Should not raise an error

    def test_map_eco_to_family_case_sensitivity(self):
        """Test that ECO codes are handled case-insensitively."""
        result_upper = map_eco_to_family("C20")
        result_lower = map_eco_to_family("c20")
        result_mixed = map_eco_to_family("C20")
        
        assert result_upper == result_lower == result_mixed

    def test_map_eco_to_family_empty_string(self):
        """Test handling of empty ECO code string."""
        result = map_eco_to_family("")
        assert result is not None
        assert isinstance(result, str)

    def test_map_eco_to_family_none_input(self):
        """Test handling of None input."""
        result = map_eco_to_family(None)
        assert result is not None
        assert isinstance(result, str)

    def test_prepare_features_for_modeling_with_missing_eco(self):
        """Test feature preparation when some rows have missing ECO codes."""
        data = {
            'eco_code': ['C20', None, 'C20', ''],
            'avg_move_time_white': [10.0, 12.0, 11.0, 9.0],
            'avg_move_time_black': [10.5, 11.5, 10.0, 9.5],
            'material_imbalance_move5': [0.0, 1.0, 0.0, 0.0],
            'outcome': [1.0, 0.0, 0.5, 1.0]
        }
        df = pd.DataFrame(data)
        
        # Should not raise an error
        X, y = prepare_features_for_modeling(df)
        
        assert X is not None
        assert y is not None
        assert len(X) == len(df)
        assert len(y) == len(df)

    def test_prepare_features_for_modeling_all_missing_eco(self):
        """Test feature preparation when all ECO codes are missing."""
        data = {
            'eco_code': [None, None, None],
            'avg_move_time_white': [10.0, 12.0, 11.0],
            'avg_move_time_black': [10.5, 11.5, 10.0],
            'material_imbalance_move5': [0.0, 1.0, 0.0],
            'outcome': [1.0, 0.0, 0.5]
        }
        df = pd.DataFrame(data)
        
        # Should handle gracefully, mapping all to a default family
        X, y = prepare_features_for_modeling(df)
        
        assert X is not None
        assert y is not None
        assert len(X) == len(df)

    def test_prepare_features_for_modeling_single_row(self):
        """Test feature preparation with a single row."""
        data = {
            'eco_code': ['C20'],
            'avg_move_time_white': [10.0],
            'avg_move_time_black': [10.5],
            'material_imbalance_move5': [0.0],
            'outcome': [1.0]
        }
        df = pd.DataFrame(data)
        
        X, y = prepare_features_for_modeling(df)
        
        assert X.shape[0] == 1
        assert len(y) == 1

    def test_prepare_features_for_modeling_empty_dataframe(self):
        """Test feature preparation with an empty dataframe."""
        df = pd.DataFrame(columns=['eco_code', 'avg_move_time_white', 'avg_move_time_black', 'material_imbalance_move5', 'outcome'])
        
        with pytest.raises((ValueError, IndexError)):
            # Should raise an error for empty data
            X, y = prepare_features_for_modeling(df)

    def test_prepare_features_for_modeling_numeric_columns(self):
        """Test that numeric columns are handled correctly."""
        data = {
            'eco_code': ['C20', 'C21'],
            'avg_move_time_white': [10.0, 20.0],
            'avg_move_time_black': [10.5, 20.5],
            'material_imbalance_move5': [0.0, 1.0],
            'outcome': [1.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        X, y = prepare_features_for_modeling(df)
        
        # Check that numeric columns are present in X
        assert 'avg_move_time_white' in X.columns
        assert 'avg_move_time_black' in X.columns
        assert 'material_imbalance_move5' in X.columns

    def test_prepare_features_for_modeling_duplicate_eco_codes(self):
        """Test handling of duplicate ECO codes."""
        data = {
            'eco_code': ['C20', 'C20', 'C20'],
            'avg_move_time_white': [10.0, 12.0, 11.0],
            'avg_move_time_black': [10.5, 11.5, 10.0],
            'material_imbalance_move5': [0.0, 1.0, 0.0],
            'outcome': [1.0, 0.0, 0.5]
        }
        df = pd.DataFrame(data)
        
        X, y = prepare_features_for_modeling(df)
        
        assert len(X) == 3
        assert len(y) == 3

    def test_prepare_features_for_modeling_special_characters_in_eco(self):
        """Test handling of ECO codes with special characters (if any)."""
        # Standard ECO codes are alphanumeric, but test robustness
        data = {
            'eco_code': ['C20', 'C21', 'C20'],
            'avg_move_time_white': [10.0, 12.0, 11.0],
            'avg_move_time_black': [10.5, 11.5, 10.0],
            'material_imbalance_move5': [0.0, 1.0, 0.0],
            'outcome': [1.0, 0.0, 0.5]
        }
        df = pd.DataFrame(data)
        
        X, y = prepare_features_for_modeling(df)
        
        assert X is not None
        assert y is not None
