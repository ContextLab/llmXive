import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest import handle_missing_values

class TestHandleMissingValues:
    """Unit tests for T012: handle_missing_values logic."""

    def test_drop_missing_required_predictors(self):
        """Test that records with missing required predictors are dropped."""
        # Create test data with missing required predictors
        data = {
            'pulse_duration': [10.0, 20.0, np.nan, 40.0],
            'power': [100.0, np.nan, 300.0, 400.0],
            'scanning_speed': [500.0, 600.0, 700.0, np.nan],
            'pattern_geometry': ['grid', 'line', 'circle', 'grid'],
            'hardness': [200.0, 250.0, 300.0, 350.0],
            'elastic_modulus': [100.0, 120.0, 140.0, 160.0],
            'contact_load': [10.0, 20.0, 30.0, 40.0],
            'wear_rate': [0.1, 0.2, 0.3, 0.4]
        }
        df = pd.DataFrame(data)
        
        # Execute handle_missing_values
        result = handle_missing_values(df)
        
        # Should have dropped 3 records (rows 2, 3, 4 in original)
        # Only row 0 has all required predictors
        assert len(result) == 1, f"Expected 1 record, got {len(result)}"
        assert result.iloc[0]['pulse_duration'] == 10.0

    def test_retain_missing_optional_predictors(self):
        """Test that records with missing optional predictors are retained with normalization_method='raw'."""
        data = {
            'pulse_duration': [10.0, 20.0, 30.0],
            'power': [100.0, 200.0, 300.0],
            'scanning_speed': [500.0, 600.0, 700.0],
            'pattern_geometry': ['grid', 'line', 'circle'],
            'hardness': [200.0, 250.0, 300.0],
            'elastic_modulus': [100.0, 120.0, 140.0],
            'contact_load': [10.0, np.nan, 30.0],  # Row 1 missing contact_load
            'sliding_speed': [np.nan, 20.0, 30.0],  # Row 0 missing sliding_speed
            'wear_rate': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # All 3 records should be retained (no missing required predictors)
        assert len(result) == 3
        
        # Check normalization_method flags
        assert result.iloc[0]['normalization_method'] == 'raw', "Row 0 should be 'raw' (missing sliding_speed)"
        assert result.iloc[1]['normalization_method'] == 'raw', "Row 1 should be 'raw' (missing contact_load)"
        assert result.iloc[2]['normalization_method'] == 'normalized', "Row 2 should be 'normalized'"

    def test_all_predictors_present(self):
        """Test that records with all predictors present are marked as 'normalized'."""
        data = {
            'pulse_duration': [10.0, 20.0],
            'power': [100.0, 200.0],
            'scanning_speed': [500.0, 600.0],
            'pattern_geometry': ['grid', 'line'],
            'hardness': [200.0, 250.0],
            'elastic_modulus': [100.0, 120.0],
            'contact_load': [10.0, 20.0],
            'sliding_speed': [5.0, 6.0],
            'wear_rate': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        assert len(result) == 2
        assert all(result['normalization_method'] == 'normalized')

    def test_missing_required_column_raises_error(self):
        """Test that missing required predictor columns raise ValueError."""
        data = {
            'pulse_duration': [10.0, 20.0],
            'power': [100.0, 200.0],
            # Missing scanning_speed
            'pattern_geometry': ['grid', 'line'],
            'hardness': [200.0, 250.0],
            'elastic_modulus': [100.0, 120.0],
            'wear_rate': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError) as exc_info:
            handle_missing_values(df)
        
        assert 'scanning_speed' in str(exc_info.value)

    def test_output_has_normalization_method_column(self):
        """Test that output DataFrame contains normalization_method column."""
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [500.0],
            'pattern_geometry': ['grid'],
            'hardness': [200.0],
            'elastic_modulus': [100.0],
            'wear_rate': [0.1]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        assert 'normalization_method' in result.columns
        assert result['normalization_method'].iloc[0] == 'normalized'

    def test_schema_compliance_with_mock_data(self):
        """Test handling of mock data with mixed missing values."""
        # Simulate T009b mock data structure
        data = {
            'pulse_duration': [10.0, 20.0, np.nan, 40.0, 50.0],
            'power': [100.0, 200.0, 300.0, np.nan, 500.0],
            'scanning_speed': [500.0, 600.0, 700.0, 800.0, np.nan],
            'pattern_geometry': ['grid', 'line', 'circle', 'grid', 'line'],
            'hardness': [200.0, 250.0, 300.0, 350.0, 400.0],
            'elastic_modulus': [100.0, 120.0, 140.0, 160.0, 180.0],
            'contact_load': [10.0, np.nan, 30.0, 40.0, 50.0],
            'sliding_speed': [np.nan, 20.0, 30.0, 40.0, 50.0],
            'wear_rate': [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # Expected:
        # Row 0: All required present, missing contact_load/sliding_speed -> raw
        # Row 1: All required present, missing contact_load/sliding_speed -> raw
        # Row 2: Missing pulse_duration -> DROP
        # Row 3: Missing power -> DROP
        # Row 4: Missing scanning_speed -> DROP
        
        assert len(result) == 2
        assert result.iloc[0]['normalization_method'] == 'raw'
        assert result.iloc[1]['normalization_method'] == 'raw'