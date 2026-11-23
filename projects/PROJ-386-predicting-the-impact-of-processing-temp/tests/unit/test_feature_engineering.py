import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.preprocessing import generate_interaction_features

class TestInteractionFeatureGeneration:
    
    def test_basic_interaction_creation(self):
        """
        T017: Unit test for interaction feature generation.
        Verify `Temp × Mg` column creation.
        """
        # Create mock data
        data = {
            'rolling_temperature': [300.0, 400.0, 500.0],
            'mg': [1.0, 2.0, 3.0],
            'si': [0.5, 1.0, 1.5],
            'grain_size': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        # Run function
        result = generate_interaction_features(df)
        
        # Verify columns exist
        assert 'rolling_temperature_x_mg' in result.columns
        assert 'rolling_temperature_x_si' in result.columns
        
        # Verify values
        expected_mg = [300.0, 800.0, 1500.0]
        assert list(result['rolling_temperature_x_mg']) == expected_mg
        
        expected_si = [150.0, 400.0, 750.0]
        assert list(result['rolling_temperature_x_si']) == expected_si

    def test_missing_temperature_column(self):
        """Test that ValueError is raised if temperature column is missing."""
        data = {
            'mg': [1.0, 2.0],
            'grain_size': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Could not identify the temperature column"):
            generate_interaction_features(df)

    def test_missing_composition_columns(self):
        """Test that ValueError is raised if no composition columns are found."""
        data = {
            'rolling_temperature': [300.0, 400.0],
            'grain_size': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="No alloy composition columns"):
            generate_interaction_features(df)

    def test_non_numeric_handling(self):
        """Test that non-numeric values are handled (coerced to NaN)."""
        data = {
            'rolling_temperature': [300.0, 'invalid', 500.0],
            'mg': [1.0, 2.0, 3.0],
            'grain_size': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        result = generate_interaction_features(df)
        
        # Check that the interaction column exists
        assert 'rolling_temperature_x_mg' in result.columns
        
        # Check that the invalid row resulted in NaN
        assert pd.isna(result.loc[1, 'rolling_temperature_x_mg'])
        
        # Check valid rows
        assert result.loc[0, 'rolling_temperature_x_mg'] == 300.0
        assert result.loc[2, 'rolling_temperature_x_mg'] == 1500.0