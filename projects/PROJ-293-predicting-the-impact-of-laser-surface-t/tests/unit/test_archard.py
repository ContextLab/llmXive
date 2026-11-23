import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingest import archard_normalization

class TestKCalculation:
    """Test suite for T013c: Archard Normalization"""

    def test_k_calculation_basic(self):
        """Test basic K calculation with valid inputs."""
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [50.0],
            'pattern_geometry': ['grid'],
            'hardness': [500.0],
            'elastic_modulus': [200.0],
            'wear_rate': [10.0],       # Volume V
            'density': [7.8],          # g/cm3
            'geometry': ['flat'],
            'contact_load': [10.0],    # N
            'sliding_speed': [100.0]   # mm/s
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        assert 'wear_coefficient_K' in result.columns
        assert 'normalization_method' in result.columns
        
        # K = (V * H) / (F_N * L) = (10 * 500) / (10 * 100) = 5000 / 1000 = 5.0
        expected_k = 5.0
        assert np.isclose(result['wear_coefficient_K'].iloc[0], expected_k)
        assert result['normalization_method'].iloc[0] == 'normalized'

    def test_missing_contact_load_flagged_raw(self):
        """Test that missing contact_load results in 'raw' flag."""
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [50.0],
            'pattern_geometry': ['grid'],
            'hardness': [500.0],
            'elastic_modulus': [200.0],
            'wear_rate': [10.0],
            'density': [7.8],
            'geometry': ['flat'],
            'contact_load': [np.nan],  # Missing
            'sliding_speed': [100.0]
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        assert pd.isna(result['wear_coefficient_K'].iloc[0])
        assert result['normalization_method'].iloc[0] == 'raw'

    def test_missing_sliding_speed_flagged_raw(self):
        """Test that missing sliding_speed results in 'raw' flag."""
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [50.0],
            'pattern_geometry': ['grid'],
            'hardness': [500.0],
            'elastic_modulus': [200.0],
            'wear_rate': [10.0],
            'density': [7.8],
            'geometry': ['flat'],
            'contact_load': [10.0],
            'sliding_speed': [np.nan]  # Missing
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        assert pd.isna(result['wear_coefficient_K'].iloc[0])
        assert result['normalization_method'].iloc[0] == 'raw'

    def test_zero_load_handling(self):
        """Test that zero contact_load results in 'raw' flag (division by zero)."""
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [50.0],
            'pattern_geometry': ['grid'],
            'hardness': [500.0],
            'elastic_modulus': [200.0],
            'wear_rate': [10.0],
            'density': [7.8],
            'geometry': ['flat'],
            'contact_load': [0.0],     # Zero
            'sliding_speed': [100.0]
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        # Should be NaN and flagged raw
        assert pd.isna(result['wear_coefficient_K'].iloc[0])
        assert result['normalization_method'].iloc[0] == 'raw'

    def test_missing_required_predictors_unchanged(self):
        """Test that records missing required predictors (from T012) are not re-added."""
        # T012 should have dropped these, but if they exist, K calc should handle them gracefully
        # or they should be 'raw' if required for K.
        # Here we test that if a required predictor for K (like hardness) is missing, it's 'raw'.
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [50.0],
            'pattern_geometry': ['grid'],
            'hardness': [np.nan],      # Missing hardness
            'elastic_modulus': [200.0],
            'wear_rate': [10.0],
            'density': [7.8],
            'geometry': ['flat'],
            'contact_load': [10.0],
            'sliding_speed': [100.0]
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        assert pd.isna(result['wear_coefficient_K'].iloc[0])
        assert result['normalization_method'].iloc[0] == 'raw'

    def test_mixed_records(self):
        """Test a DataFrame with a mix of normalized and raw records."""
        data = {
            'pulse_duration': [10.0, 20.0, 30.0],
            'power': [100.0, 200.0, 300.0],
            'scanning_speed': [50.0, 60.0, 70.0],
            'pattern_geometry': ['grid', 'line', 'dot'],
            'hardness': [500.0, 600.0, 700.0],
            'elastic_modulus': [200.0, 210.0, 220.0],
            'wear_rate': [10.0, 20.0, 30.0],
            'density': [7.8, 7.9, 8.0],
            'geometry': ['flat', 'flat', 'flat'],
            'contact_load': [10.0, np.nan, 20.0], # Row 1 missing load
            'sliding_speed': [100.0, 100.0, np.nan] # Row 2 missing speed
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        # Row 0: Valid -> normalized
        assert result['normalization_method'].iloc[0] == 'normalized'
        # Row 1: Missing load -> raw
        assert result['normalization_method'].iloc[1] == 'raw'
        # Row 2: Missing speed -> raw
        assert result['normalization_method'].iloc[2] == 'raw'

    def test_excludes_contact_load_from_predictors_logic(self):
        """Verify that contact_load and sliding_speed are used for K but not added as K predictors."""
        # This is a logic check. The function calculates K using them, but the resulting
        # DataFrame should have K as the target, and the original columns remain.
        # The "exclusion" is for the MODELING phase (predictors), not the calculation.
        # The task says "explicitly EXCLUDE ... from the predictor feature set when the target is K".
        # This function produces the target K. The exclusion happens when selecting features for ML.
        # We verify that K is calculated and the columns exist.
        data = {
            'pulse_duration': [10.0],
            'power': [100.0],
            'scanning_speed': [50.0],
            'pattern_geometry': ['grid'],
            'hardness': [500.0],
            'elastic_modulus': [200.0],
            'wear_rate': [10.0],
            'density': [7.8],
            'geometry': ['flat'],
            'contact_load': [10.0],
            'sliding_speed': [100.0]
        }
        df = pd.DataFrame(data)
        
        result = archard_normalization(df)
        
        assert 'wear_coefficient_K' in result.columns
        assert 'contact_load' in result.columns
        assert 'sliding_speed' in result.columns
        assert result['normalization_method'].iloc[0] == 'normalized'
        # The exclusion is a modeling constraint, not a data removal here.
        # But we confirm K is computed.
