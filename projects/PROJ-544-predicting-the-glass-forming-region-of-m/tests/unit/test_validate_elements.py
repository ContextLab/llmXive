"""
Unit tests for element validation functionality.

Tests the validate_elements module to ensure proper validation of
elemental symbols against pymatgen's periodic table.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from code.descriptors.validate_elements import is_valid_element, validate_composition_elements

class TestIsValidElement:
    """Tests for the is_valid_element function."""
    
    def test_valid_elements(self):
        """Test that known valid elements return True."""
        valid_elements = ['Cu', 'Zr', 'Fe', 'Ni', 'H', 'He', 'U', 'Pu']
        for elem in valid_elements:
            assert is_valid_element(elem) is True, f"{elem} should be valid"
    
    def test_invalid_elements(self):
        """Test that invalid symbols return False."""
        invalid_elements = ['XX', 'QQ', '123', '', 'cu', 'ZZZ']
        for elem in invalid_elements:
            assert is_valid_element(elem) is False, f"{elem} should be invalid"
    
    def test_case_sensitivity(self):
        """Test that lowercase symbols are invalid."""
        assert is_valid_element('cu') is False
        assert is_valid_element('fe') is False
        assert is_valid_element('CU') is False

class TestValidateCompositionElements:
    """Tests for the validate_composition_elements function."""
    
    def test_simple_valid_composition(self):
        """Test simple valid composition string."""
        valid, invalid = validate_composition_elements('Cu50Zr50')
        assert set(valid) == {'Cu', 'Zr'}
        assert invalid == []
    
    def test_dash_separated(self):
        """Test dash-separated composition."""
        valid, invalid = validate_composition_elements('Cu-Zr')
        assert set(valid) == {'Cu', 'Zr'}
        assert invalid == []
    
    def test_comma_separated(self):
        """Test comma-separated composition."""
        valid, invalid = validate_composition_elements('Cu,Zr,Fe')
        assert set(valid) == {'Cu', 'Zr', 'Fe'}
        assert invalid == []
    
    def test_mixed_valid_invalid(self):
        """Test composition with mixed valid and invalid elements."""
        valid, invalid = validate_composition_elements('Cu-XX-Zr')
        assert set(valid) == {'Cu', 'Zr'}
        assert invalid == ['XX']
    
    def test_all_invalid(self):
        """Test composition with all invalid elements."""
        valid, invalid = validate_composition_elements('XX-QQ-RR')
        assert valid == []
        assert set(invalid) == {'XX', 'QQ', 'RR'}

class TestValidateElementsScript:
    """Integration tests for the validate_elements script."""
    
    def test_script_produces_outputs(self):
        """Test that script produces both output files."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample_id,composition,phase_label\n")
            f.write("1,Cu50Zr50,glass\n")
            f.write("2,Fe-Ni-crystalline\n")
            f.write("3,Cu-XX-Zr,glass\n")
            input_path = f.name
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                valid_output = os.path.join(tmpdir, 'valid.csv')
                invalid_output = os.path.join(tmpdir, 'invalid.csv')
                
                # Import and run main logic
                from code.descriptors.validate_elements import main
                import sys
                
                # Redirect sys.argv for argument parsing
                original_argv = sys.argv
                sys.argv = ['validate_elements.py', 
                           '--input', input_path,
                           '--output-valid', valid_output,
                           '--output-invalid', invalid_output]
                
                try:
                    result = main()
                    assert result == 0, "Script should return 0 on success"
                finally:
                    sys.argv = original_argv
                
                # Verify outputs exist
                assert os.path.exists(valid_output), "Valid output file should exist"
                assert os.path.exists(invalid_output), "Invalid output file should exist"
                
                # Verify content
                valid_df = pd.read_csv(valid_output)
                invalid_df = pd.read_csv(invalid_output)
                
                # Sample 1 (Cu50Zr50) should be valid
                assert len(valid_df) >= 1
                # Sample 3 (Cu-XX-Zr) should be invalid
                assert len(invalid_df) >= 1
        finally:
            os.unlink(input_path)
