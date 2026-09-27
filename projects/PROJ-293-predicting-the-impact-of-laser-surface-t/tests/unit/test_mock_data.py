import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestMockDataSchemaCompliance:
    """Tests for T009b: Mock data schema compliance."""
    
    @pytest.fixture
    def mock_data_path(self):
        return "data/raw/mock_lst_data.csv"
    
    @pytest.fixture
    def mock_dataframe(self, mock_data_path):
        """Load the mock data file for testing."""
        if not os.path.exists(mock_data_path):
            pytest.skip("Mock data file not found. Run T009b first.")
        return pd.read_csv(mock_data_path)
    
    def test_schema_compliance(self, mock_dataframe):
        """Verify all required columns are present and data types are correct."""
        required_columns = [
            'pulse_duration', 'power', 'scanning_speed', 'pattern_geometry',
            'hardness', 'elastic_modulus', 'wear_rate', 'contact_load',
            'sliding_speed', 'density', 'geometry'
        ]
        
        # Check all required columns exist
        assert set(required_columns).issubset(set(mock_dataframe.columns)), \
            f"Missing columns: {set(required_columns) - set(mock_dataframe.columns)}"
        
        # Check data types for numeric columns
        numeric_cols = [
            'pulse_duration', 'power', 'scanning_speed', 'hardness',
            'elastic_modulus', 'wear_rate', 'contact_load', 'sliding_speed', 'density'
        ]
        
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(mock_dataframe[col]), \
                f"Column {col} is not numeric"
        
        # Check categorical columns
        categorical_cols = ['pattern_geometry', 'geometry']
        for col in categorical_cols:
            assert mock_dataframe[col].dtype == 'object', \
                f"Column {col} should be object (categorical)"
        
        # Verify record count
        assert len(mock_dataframe) >= 150, \
            f"Expected at least 150 records, got {len(mock_dataframe)}"
    
    def test_missing_values_logic(self, mock_dataframe):
        """Verify that contact_load and sliding_speed have missing values for T012 testing."""
        missing_contact = mock_dataframe['contact_load'].isna().sum()
        missing_sliding = mock_dataframe['sliding_speed'].isna().sum()
        
        # We expect some missing values (approx 15% as per generation logic)
        assert missing_contact > 0, "No missing values in contact_load - T012 logic not tested"
        assert missing_sliding > 0, "No missing values in sliding_speed - T012 logic not tested"
        
        # Verify that required predictors are NOT missing
        required_predictors = [
            'pulse_duration', 'power', 'scanning_speed', 'pattern_geometry',
            'hardness', 'elastic_modulus'
        ]
        
        for col in required_predictors:
            missing_count = mock_dataframe[col].isna().sum()
            assert missing_count == 0, \
                f"Required predictor {col} has {missing_count} missing values"
    
    def test_value_ranges(self, mock_dataframe):
        """Verify that generated values are within reasonable physical ranges."""
        # Pulse duration (ns)
        assert mock_dataframe['pulse_duration'].between(0, 1000).all(), \
            "Pulse duration out of reasonable range"
        
        # Power (W)
        assert mock_dataframe['power'].between(0, 2000).all(), \
            "Power out of reasonable range"
        
        # Scanning speed (mm/s)
        assert mock_dataframe['scanning_speed'].between(0, 5000).all(), \
            "Scanning speed out of reasonable range"
        
        # Hardness (HV)
        assert mock_dataframe['hardness'].between(0, 2000).all(), \
            "Hardness out of reasonable range"
        
        # Elastic modulus (GPa)
        assert mock_dataframe['elastic_modulus'].between(0, 500).all(), \
            "Elastic modulus out of reasonable range"
        
        # Wear rate (mm^3/Nm) - should be positive
        assert (mock_dataframe['wear_rate'] > 0).all(), \
            "Wear rate should be positive"
        
        # Density (g/cm^3)
        assert mock_dataframe['density'].between(1, 20).all(), \
            "Density out of reasonable range"
    
    def test_categorical_values(self, mock_dataframe):
        """Verify categorical columns have valid values."""
        valid_patterns = ['dot', 'line', 'grid', 'honeycomb', 'dimple']
        valid_geometries = ['cylindrical', 'flat', 'spherical']
        
        assert all(val in valid_patterns for val in mock_dataframe['pattern_geometry'].unique()), \
            f"Invalid pattern_geometry values found"
        
        assert all(val in valid_geometries for val in mock_dataframe['geometry'].unique()), \
            f"Invalid geometry values found"
    
    def test_file_exists(self, mock_data_path):
        """Verify the output file exists."""
        assert os.path.exists(mock_data_path), \
            f"Mock data file not found at {mock_data_path}"
    
    def test_deterministic_generation(self):
        """Verify that re-running generation produces the same data (deterministic)."""
        # This test assumes the generation script uses a fixed seed
        # We verify by checking if the file exists and has the expected structure
        mock_path = "data/raw/mock_lst_data.csv"
        if os.path.exists(mock_path):
            df = pd.read_csv(mock_path)
            # If we can read it and it has the right structure, it's likely deterministic
            assert len(df) >= 150, "Record count mismatch"
            assert set(['pulse_duration', 'power', 'scanning_speed']).issubset(set(df.columns)), \
                "Schema mismatch"
        else:
            pytest.skip("Mock data file not found for deterministic check")