"""
Unit tests for preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocess import (
    parse_composition_string,
    weight_to_atomic_percent,
    normalize_composition,
    check_required_fields,
    preprocess_data
)

class TestParseCompositionString:
    """Tests for composition string parsing."""
    
    def test_format_colon_comma(self):
        """Test parsing 'Fe:0.8,Cr:0.1,Ni:0.1' format."""
        result = parse_composition_string("Fe:0.8,Cr:0.1,Ni:0.1")
        assert 'Fe' in result
        assert abs(result['Fe'] - 0.8) < 0.001
        assert abs(result['Cr'] - 0.1) < 0.001
        assert abs(result['Ni'] - 0.1) < 0.001
    
    def test_format_hyphen(self):
        """Test parsing 'Fe-0.8Cr-0.1Ni-0.1' format."""
        result = parse_composition_string("Fe-0.8Cr-0.1Ni-0.1")
        assert 'Fe' in result
        assert abs(result['Fe'] - 0.8) < 0.001
    
    def test_format_concatenated(self):
        """Test parsing 'Fe80Cr10Ni10' format."""
        result = parse_composition_string("Fe80Cr10Ni10")
        assert 'Fe' in result
        assert abs(result['Fe'] - 80.0) < 0.001
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = parse_composition_string("")
        assert result == {}
    
    def test_none_input(self):
        """Test handling of None input."""
        result = parse_composition_string(None)
        assert result == {}
    
    def test_invalid_format(self):
        """Test handling of invalid format."""
        result = parse_composition_string("invalid")
        assert result == {}

class TestWeightToAtomicPercent:
    """Tests for weight to atomic percent conversion."""
    
    def test_simple_binary(self):
        """Test conversion for simple binary alloy."""
        # 50wt% Fe, 50wt% Cr
        # Moles Fe = 50/55.845 = 0.895
        # Moles Cr = 50/51.996 = 0.962
        # Total = 1.857
        # At% Fe = 0.895/1.857 = 48.2%
        # At% Cr = 0.962/1.857 = 51.8%
        composition = {'Fe': 50.0, 'Cr': 50.0}
        result = weight_to_atomic_percent(composition)
        
        assert 'Fe' in result
        assert 'Cr' in result
        assert abs(result['Fe'] + result['Cr'] - 100.0) < 0.01
    
    def test_empty_input(self):
        """Test conversion for empty input."""
        result = weight_to_atomic_percent({})
        assert result == {}
    
    def test_unknown_element(self):
        """Test conversion with unknown element."""
        composition = {'Fe': 50.0, 'Unknown': 50.0}
        result = weight_to_atomic_percent(composition)
        # Should only contain known elements
        assert 'Fe' in result
        assert 'Unknown' not in result

class TestNormalizeComposition:
    """Tests for composition normalization."""
    
    def test_sorting(self):
        """Test that elements are sorted alphabetically."""
        composition = {'Ni': 10.0, 'Fe': 80.0, 'Cr': 10.0}
        result = normalize_composition(composition)
        
        # Should be Cr, Fe, Ni order
        assert result.index('Cr') < result.index('Fe')
        assert result.index('Fe') < result.index('Ni')
    
    def test_rounding(self):
        """Test that values are rounded correctly."""
        composition = {'Fe': 33.333333, 'Cr': 33.333333, 'Ni': 33.333334}
        result = normalize_composition(composition, decimals=2)
        
        assert '33.33' in result
    
    def test_empty_input(self):
        """Test normalization of empty input."""
        result = normalize_composition({})
        assert result == ""

class TestCheckRequiredFields:
    """Tests for required field checking."""
    
    def test_valid_row(self):
        """Test detection of valid row."""
        row = pd.Series({
            'alloy_id': 1,
            'composition_str': 'Fe:0.8,Cr:0.1',
            'temperature': 800.0,
            'stress': 100.0,
            'rupture_time': 1000.0
        })
        is_valid, missing = check_required_fields(row)
        assert is_valid
        assert len(missing) == 0
    
    def test_missing_temperature(self):
        """Test detection of missing temperature."""
        row = pd.Series({
            'alloy_id': 1,
            'composition_str': 'Fe:0.8,Cr:0.1',
            'temperature': None,
            'stress': 100.0,
            'rupture_time': 1000.0
        })
        is_valid, missing = check_required_fields(row)
        assert not is_valid
        assert 'temperature' in missing
    
    def test_missing_composition(self):
        """Test detection of missing composition."""
        row = pd.Series({
            'alloy_id': 1,
            'composition_str': None,
            'temperature': 800.0,
            'stress': 100.0,
            'rupture_time': 1000.0
        })
        is_valid, missing = check_required_fields(row)
        assert not is_valid
        assert 'composition_str' in missing

class TestPreprocessData:
    """Integration tests for preprocess_data function."""
    
    def test_full_pipeline(self):
        """Test complete preprocessing pipeline."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("alloy_id,composition_str,temperature,stress,rupture_time\n")
            f.write("1,Fe:0.8,Cr:0.1,Ni:0.1,800.0,100.0,1000.0\n")
            f.write("2,Fe:0.7,Cr:0.2,Ni:0.1,850.0,150.0,2000.0\n")
            input_path = f.name
        
        output_path = input_path.replace('.csv', '_processed.csv')
        
        try:
            stats = preprocess_data(input_path, output_path)
            
            assert stats['total_rows'] == 2
            assert stats['final_rows'] == 2
            assert stats['excluded_missing_fields'] == 0
            
            # Verify output file exists
            assert Path(output_path).exists()
            
            # Verify output content
            df = pd.read_csv(output_path)
            assert len(df) == 2
            assert 'composition_str' in df.columns
            # Check that composition is normalized (sorted alphabetically)
            assert df.iloc[0]['composition_str'].startswith('Cr:')
        finally:
            # Cleanup
            if Path(input_path).exists():
                os.remove(input_path)
            if Path(output_path).exists():
                os.remove(output_path)
    
    def test_exclusion_logic(self):
        """Test that rows with missing fields are excluded."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("alloy_id,composition_str,temperature,stress,rupture_time\n")
            f.write("1,Fe:0.8,Cr:0.1,800.0,100.0,1000.0\n")  # Valid
            f.write("2,Fe:0.7,Cr:0.2,,150.0,2000.0\n")  # Missing temperature
            f.write("3,,800.0,100.0,1000.0\n")  # Missing composition
            input_path = f.name
        
        output_path = input_path.replace('.csv', '_processed.csv')
        
        try:
            stats = preprocess_data(input_path, output_path)
            
            assert stats['total_rows'] == 3
            assert stats['final_rows'] == 1
            assert stats['excluded_missing_fields'] == 2
            
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df.iloc[0]['alloy_id'] == 1
        finally:
            if Path(input_path).exists():
                os.remove(input_path)
            if Path(output_path).exists():
                os.remove(output_path)