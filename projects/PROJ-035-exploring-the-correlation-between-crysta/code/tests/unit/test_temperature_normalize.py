"""
Unit tests for temperature normalization module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cleaning.temperature_normalize import (
    slack_normalization_factor,
    is_within_reference_window,
    is_unknown_temperature,
    normalize_thermal_conductivity,
    normalize_dataframe,
    apply_temperature_normalization,
    REFERENCE_TEMPERATURE,
    TEMPERATURE_TOLERANCE,
    DEFAULT_EXPONENT
)


class TestSlackNormalizationFactor:
    """Tests for slack_normalization_factor function."""
    
    def test_normal_case(self):
        """Test standard normalization factor calculation."""
        T = 400.0
        T_ref = 300.0
        n = 1.5
        
        factor = slack_normalization_factor(T, T_ref, n)
        expected = (T_ref / T) ** n
        
        assert abs(factor - expected) < 1e-10
    
    def test_at_reference_temperature(self):
        """Test that factor is 1.0 at reference temperature."""
        factor = slack_normalization_factor(300.0, 300.0, 1.5)
        assert abs(factor - 1.0) < 1e-10
    
    def test_negative_temperature_raises(self):
        """Test that negative temperature raises ValueError."""
        with pytest.raises(ValueError, match="Temperature must be positive"):
            slack_normalization_factor(-100.0, 300.0, 1.5)
    
    def test_zero_temperature_raises(self):
        """Test that zero temperature raises ValueError."""
        with pytest.raises(ValueError, match="Temperature must be positive"):
            slack_normalization_factor(0.0, 300.0, 1.5)
    
    def test_negative_reference_raises(self):
        """Test that negative reference temperature raises ValueError."""
        with pytest.raises(ValueError, match="Reference temperature must be positive"):
            slack_normalization_factor(300.0, -300.0, 1.5)

class TestNormalizeThermalConductivity:
    """Tests for normalize_thermal_conductivity function."""
    
    def test_normalization_at_higher_temp(self):
        """Test normalization from higher temperature to reference."""
        k = 10.0  # W/mK at 400K
        T = 400.0
        T_ref = 300.0
        n = 1.5
        
        k_normalized = normalize_thermal_conductivity(k, T, T_ref, n)
        
        # k_normalized should be k * (T_ref/T)^n
        expected = k * slack_normalization_factor(T, T_ref, n)
        
        assert abs(k_normalized - expected) < 1e-10
        # Since T > T_ref, normalized k should be higher
        assert k_normalized > k
    
    def test_normalization_at_lower_temp(self):
        """Test normalization from lower temperature to reference."""
        k = 10.0  # W/mK at 200K
        T = 200.0
        T_ref = 300.0
        n = 1.5
        
        k_normalized = normalize_thermal_conductivity(k, T, T_ref, n)
        
        # Since T < T_ref, normalized k should be lower
        assert k_normalized < k

class TestIsWithinReferenceWindow:
    """Tests for is_within_reference_window function."""
    
    def test_within_window(self):
        """Test temperature within tolerance window."""
        assert is_within_reference_window(305.0, 300.0, 10.0) is True
        assert is_within_reference_window(295.0, 300.0, 10.0) is True
        assert is_within_reference_window(310.0, 300.0, 10.0) is True
        assert is_within_reference_window(290.0, 300.0, 10.0) is True
    
    def test_outside_window(self):
        """Test temperature outside tolerance window."""
        assert is_within_reference_window(311.0, 300.0, 10.0) is False
        assert is_within_reference_window(289.0, 300.0, 10.0) is False
    
    def test_boundary_conditions(self):
        """Test exact boundary conditions."""
        assert is_within_reference_window(310.0, 300.0, 10.0) is True
        assert is_within_reference_window(290.0, 300.0, 10.0) is True

class TestIsUnknownTemperature:
    """Tests for is_unknown_temperature function."""
    
    def test_none_value(self):
        """Test None is unknown."""
        assert is_unknown_temperature(None) is True
    
    def test_nan_value(self):
        """Test NaN is unknown."""
        assert is_unknown_temperature(np.nan) is True
    
    def test_na_string(self):
        """Test 'N/A' string is unknown."""
        assert is_unknown_temperature('N/A') is True
        assert is_unknown_temperature('n/a') is True
        assert is_unknown_temperature('N/a') is True
    
    def test_unknown_string(self):
        """Test 'unknown' string is unknown."""
        assert is_unknown_temperature('unknown') is True
        assert is_unknown_temperature('UNKNOWN') is True
    
    def test_none_string(self):
        """Test 'None' string is unknown."""
        assert is_unknown_temperature('None') is True
        assert is_unknown_temperature('none') is True
    
    def test_empty_string(self):
        """Test empty string is unknown."""
        assert is_unknown_temperature('') is True
        assert is_unknown_temperature('   ') is True
    
    def test_negative_one(self):
        """Test -1 is unknown."""
        assert is_unknown_temperature(-1) is True
        assert is_unknown_temperature(-1.0) is True
    
    def test_valid_temperature(self):
        """Test valid temperature is not unknown."""
        assert is_unknown_temperature(300.0) is False
        assert is_unknown_temperature(295.5) is True is False
        assert is_unknown_temperature(400) is False

class TestNormalizeDataFrame:
    """Tests for normalize_dataframe function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.df = pd.DataFrame({
            'structure_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'thermal_conductivity': [10.0, 15.0, 12.0, 8.0, 20.0],
            'temperature': [300.0, 400.0, 200.0, 305.0, np.nan],
            'source': ['A', 'B', 'C', 'D', 'E']
        })
    
    def test_basic_normalization(self):
        """Test basic DataFrame normalization."""
        result_df, discarded, corrected = normalize_dataframe(
            self.df.copy(),
            temperature_col='temperature',
            thermal_col='thermal_conductivity'
        )
        
        # NaN temperature should be discarded
        assert discarded == 1
        # Temperature outside window (400K, 200K) should be corrected
        assert corrected == 2
        # Final dataframe should have 4 rows
        assert len(result_df) == 4
    
    def test_unknown_temperature_values(self):
        """Test handling of various unknown temperature values."""
        df_with_unknowns = pd.DataFrame({
            'id': ['1', '2', '3', '4', '5', '6', '7'],
            'k': [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            'temp': [300.0, 'N/A', 'unknown', -1, '', None, 305.0]
        })
        
        result_df, discarded, corrected = normalize_dataframe(
            df_with_unknowns,
            temperature_col='temp',
            thermal_col='k'
        )
        
        # 5 unknown values should be discarded (N/A, unknown, -1, '', None)
        assert discarded == 5
        # Only 2 rows remain (300.0 and 305.0)
        assert len(result_df) == 2
    
    def test_missing_temperature_column(self):
        """Test error when temperature column is missing."""
        with pytest.raises(ValueError, match="Temperature column"):
            normalize_dataframe(
                self.df.copy(),
                temperature_col='nonexistent',
                thermal_col='thermal_conductivity'
            )
    
    def test_missing_thermal_column(self):
        """Test error when thermal conductivity column is missing."""
        with pytest.raises(ValueError, match="Thermal conductivity column"):
            normalize_dataframe(
                self.df.copy(),
                temperature_col='temperature',
                thermal_col='nonexistent'
            )
    
    def test_all_within_window(self):
        """Test when all temperatures are within the reference window."""
        df_within = pd.DataFrame({
            'id': ['1', '2', '3'],
            'k': [10.0, 15.0, 12.0],
            'temp': [295.0, 305.0, 300.0]
        })
        
        result_df, discarded, corrected = normalize_dataframe(
            df_within,
            temperature_col='temp',
            thermal_col='k'
        )
        
        assert discarded == 0
        assert corrected == 0
        assert len(result_df) == 3
        # Values should be unchanged
        assert result_df['k'].tolist() == [10.0, 15.0, 12.0]

class TestApplyTemperatureNormalization:
    """Tests for apply_temperature_normalization function."""
    
    def test_full_pipeline(self):
        """Test complete normalization pipeline with file I/O."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            
            # Create input data
            df_input = pd.DataFrame({
                'structure_id': ['S1', 'S2', 'S3', 'S4'],
                'thermal_conductivity': [10.0, 15.0, 12.0, 8.0],
                'temperature': [300.0, 400.0, 200.0, 305.0],
                'source': ['A', 'B', 'C', 'D']
            })
            df_input.to_csv(input_path, index=False)
            
            # Run normalization
            stats = apply_temperature_normalization(
                input_path=str(input_path),
                output_path=str(output_path)
            )
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify statistics
            assert stats['input_rows'] == 4
            assert stats['output_rows'] == 4
            assert stats['discarded_unknown_temp'] == 0
            assert stats['normalized_outside_window'] == 2
            
            # Verify output data
            df_output = pd.read_csv(output_path)
            assert len(df_output) == 4
            
            # Check that temperatures outside window were normalized to 300K
            temps = df_output['temperature'].tolist()
            assert all(t == 300.0 for t in temps)
    
    def test_file_not_found(self):
        """Test error when input file does not exist."""
        with pytest.raises(FileNotFoundError):
            apply_temperature_normalization(
                input_path='/nonexistent/file.csv',
                output_path='/tmp/output.csv'
            )
    
    def test_seed_parameter(self):
        """Test that seed parameter is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            
            df_input = pd.DataFrame({
                'id': ['1', '2'],
                'k': [10.0, 15.0],
                'temp': [300.0, 305.0]
            })
            df_input.to_csv(input_path, index=False)
            
            # Should not raise
            stats = apply_temperature_normalization(
                input_path=str(input_path),
                output_path=str(output_path),
                seed=42
            )
            
            assert stats is not None

class TestIntegration:
    """Integration tests for the temperature normalization module."""
    
    def test_end_to_end_with_realistic_data(self):
        """Test end-to-end normalization with realistic perovskite thermal data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'thermal_raw.csv'
            output_path = Path(tmpdir) / 'normalized_thermal.csv'
            
            # Simulate realistic thermal conductivity data
            df_input = pd.DataFrame({
                'structure_id': [f'mp-{i}' for i in range(100, 115)],
                'thermal_conductivity': np.random.uniform(5.0, 25.0, 15),
                'temperature': [300.0, 305.0, 295.0, 400.0, 200.0, 350.0, 250.0, 
                               310.0, 290.0, 'N/A', 300.0, 450.0, 150.0, -1, 305.0],
                'source_reference': [f'DOI:10.1000/journal.{i}' for i in range(15)],
                'chemistry_class': ['oxide'] * 10 + ['halide'] * 5
            })
            
            df_input.to_csv(input_path, index=False)
            
            # Run normalization
            stats = apply_temperature_normalization(
                input_path=str(input_path),
                output_path=str(output_path),
                seed=42
            )
            
            # Verify output
            assert output_path.exists()
            df_output = pd.read_csv(output_path)
            
            # Should have discarded 3 unknown temperatures (N/A, -1, and one NaN if any)
            assert stats['discarded_unknown_temp'] >= 2
            assert len(df_output) == 15 - stats['discarded_unknown_temp']
            
            # All remaining temperatures should be 300.0 (normalized)
            assert all(df_output['temperature'] == 300.0)
            
            # Verify JSON report can be generated
            report_path = Path(tmpdir) / 'normalization_report.json'
            with open(report_path, 'w') as f:
                json.dump(stats, f, indent=2)
            
            assert report_path.exists()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])