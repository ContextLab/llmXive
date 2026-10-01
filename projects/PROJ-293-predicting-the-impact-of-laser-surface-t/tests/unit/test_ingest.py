import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from ingest import handle_missing_values

class TestMissingPredictorHandling:
    """
    Tests for T012: handle_missing_values function.
    Verifies that records with missing required predictors are dropped,
    while records with missing optional predictors (contact_load, sliding_speed) are retained.
    """

    def setup_method(self):
        """Setup test data for each test case."""
        self.required_predictors = [
            'pulse_duration', 'power', 'scanning_speed', 
            'pattern_geometry', 'hardness', 'elastic_modulus'
        ]
        self.optional_predictors = ['contact_load', 'sliding_speed']

    def test_drops_missing_required_predictor(self):
        """Test that records with missing required predictors are dropped."""
        data = {
            'pulse_duration': [10.0, np.nan, 15.0],
            'power': [100.0, 200.0, np.nan],
            'scanning_speed': [500.0, 600.0, 700.0],
            'pattern_geometry': ['grid', 'dot', 'line'],
            'hardness': [500.0, 600.0, 700.0],
            'elastic_modulus': [200.0, 210.0, 220.0],
            'wear_rate': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # Only the first row should remain (no missing required predictors)
        assert len(result) == 1
        assert result.iloc[0]['pulse_duration'] == 10.0
        assert result.iloc[0]['power'] == 100.0

    def test_retains_missing_optional_predictors(self):
        """Test that records with missing contact_load or sliding_speed are retained."""
        data = {
            'pulse_duration': [10.0, 15.0, 20.0],
            'power': [100.0, 150.0, 200.0],
            'scanning_speed': [500.0, 600.0, 700.0],
            'pattern_geometry': ['grid', 'dot', 'line'],
            'hardness': [500.0, 600.0, 700.0],
            'elastic_modulus': [200.0, 210.0, 220.0],
            'contact_load': [10.0, np.nan, 30.0],  # Row 2 missing
            'sliding_speed': [np.nan, 2.0, 3.0],   # Row 1 missing
            'wear_rate': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # All rows should be retained because only optional predictors are missing
        assert len(result) == 3

    def test_drops_if_any_required_missing(self):
        """Test that if ANY required predictor is missing, the record is dropped."""
        data = {
            'pulse_duration': [10.0, 15.0, 20.0],
            'power': [100.0, 150.0, 200.0],
            'scanning_speed': [500.0, np.nan, 700.0],  # Row 2 missing
            'pattern_geometry': ['grid', 'dot', 'line'],
            'hardness': [500.0, 600.0, 700.0],
            'elastic_modulus': [200.0, 210.0, 220.0],
            'wear_rate': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # Row 2 should be dropped
        assert len(result) == 2
        assert 'scanning_speed' not in result.iloc[1].isna().to_dict().values() or result.iloc[1]['scanning_speed'] == 700.0

    def test_normalization_method_not_present(self):
        """Test that normalization_method column is NOT present after T012 processing."""
        data = {
            'pulse_duration': [10.0, 15.0, 20.0],
            'power': [100.0, 150.0, 200.0],
            'scanning_speed': [500.0, 600.0, 700.0],
            'pattern_geometry': ['grid', 'dot', 'line'],
            'hardness': [500.0, 600.0, 700.0],
            'elastic_modulus': [200.0, 210.0, 220.0],
            'wear_rate': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # Verify normalization_method is not in columns
        assert 'normalization_method' not in result.columns

    def test_handles_all_required_missing(self):
        """Test behavior when all required predictors are missing in some rows."""
        data = {
            'pulse_duration': [10.0, np.nan, np.nan, 20.0],
            'power': [100.0, 150.0, np.nan, 200.0],
            'scanning_speed': [500.0, 600.0, np.nan, 700.0],
            'pattern_geometry': ['grid', 'dot', 'line', 'circle'],
            'hardness': [500.0, 600.0, np.nan, 700.0],
            'elastic_modulus': [200.0, 210.0, np.nan, 220.0],
            'wear_rate': [0.1, 0.2, 0.3, 0.4]
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        # Only rows 0 and 3 should remain
        assert len(result) == 2
        assert list(result['pulse_duration']) == [10.0, 20.0]

    def test_missing_all_columns_raises_error(self):
        """Test that missing required columns in schema raises ValueError."""
        data = {
            'pulse_duration': [10.0, 15.0],
            'power': [100.0, 150.0],
            'wear_rate': [0.1, 0.2]
            # Missing: scanning_speed, pattern_geometry, hardness, elastic_modulus
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError) as excinfo:
            handle_missing_values(df)
        
        assert "Missing required columns" in str(excinfo.value)