import pytest
import sympy
import os
import sys
import tempfile
import json

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.derivation.variance_scaling import (
    derive_variance_accumulation,
    verify_symmetry_and_linearity,
    save_derivation_output
)

class TestDeriveVarianceAccumulation:
    """Test suite for derive_variance_accumulation function."""

    def test_general_expression(self):
        """Test that calling without arguments returns the general symbolic expression."""
        result = derive_variance_accumulation()
        
        assert isinstance(result, sympy.Expr), "Should return a sympy expression"
        # The expression should be N * sigma^2
        n_sym = sympy.Symbol('N', integer=True, positive=True)
        sigma_sq = sympy.Symbol('sigma_sq')
        
        # Check that the expression equals N * sigma^2
        expected = n_sym * sigma_sq
        assert sympy.simplify(result - expected) == 0

    def test_with_n_substitution(self):
        """Test that providing N substitutes it into the expression."""
        N_val = 10
        result = derive_variance_accumulation(N=N_val)
        
        assert isinstance(result, dict), "Should return a dictionary when N is provided"
        assert 'expr' in result
        assert result['N'] == N_val
        
        # The expression should be 10 * sigma^2
        sigma_sq = sympy.Symbol('sigma_sq')
        expected = N_val * sigma_sq
        assert sympy.simplify(result['expr'] - expected) == 0

    def test_with_both_n_and_epsilon(self):
        """Test that providing both N and epsilon works correctly."""
        N_val = 5
        epsilon = sympy.Symbol('epsilon')
        result = derive_variance_accumulation(N=N_val, epsilon=epsilon)
        
        assert isinstance(result, dict)
        assert result['N'] == N_val
        assert 'expr' in result

    def test_invalid_n(self):
        """Test that invalid N values raise an error."""
        with pytest.raises(ValueError):
            derive_variance_accumulation(N=0)
        
        with pytest.raises(ValueError):
            derive_variance_accumulation(N=-5)
        
        with pytest.raises(ValueError):
            derive_variance_accumulation(N=3.5)

    def test_assumptions_present(self):
        """Test that assumptions are included in the result."""
        result = derive_variance_accumulation(N=10)
        
        assert 'assumptions' in result
        assert "i.i.d. noise" in result['assumptions']
        assert "independent objectives" in result['assumptions']

class TestVerifySymmetryAndLinearity:
    """Test suite for verify_symmetry_and_linearity function."""

    def test_linear_expression(self):
        """Test that a linear expression passes verification."""
        n_sym = sympy.Symbol('N', integer=True, positive=True)
        sigma_sq = sympy.Symbol('sigma_sq')
        expr = n_sym * sigma_sq
        
        is_valid, message = verify_symmetry_and_linearity(expr)
        
        assert is_valid, "Linear expression should pass verification"
        assert "satisfies" in message.lower()

    def test_non_linear_expression(self):
        """Test that a non-linear expression fails verification."""
        n_sym = sympy.Symbol('N', integer=True, positive=True)
        sigma_sq = sympy.Symbol('sigma_sq')
        # Create a non-linear expression: N^2 * sigma^2
        expr = n_sym**2 * sigma_sq
        
        is_valid, message = verify_symmetry_and_linearity(expr)
        
        assert not is_valid, "Non-linear expression should fail verification"
        assert "linear" in message.lower()

class TestSaveDerivationOutput:
    """Test suite for save_derivation_output function."""

    def test_save_to_json(self):
        """Test that derivation output is saved correctly to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_derivation.json')
            
            test_data = {
                'expr': sympy.Symbol('N') * sympy.Symbol('sigma_sq'),
                'N': 10,
                'assumptions': ['i.i.d. noise'],
                'formula': 'N * sigma^2'
            }
            
            save_derivation_output(output_path, test_data)
            
            assert os.path.exists(output_path), "Output file should be created"
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data['N'] == 10
            assert loaded_data['assumptions'] == ['i.i.d. noise']
            # Check that sympy expression was converted to string
            assert isinstance(loaded_data['expr'], str)

    def test_save_creates_directories(self):
        """Test that save_derivation_output creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, 'subdir', 'nested', 'output.json')
            
            test_data = {
                'expr': sympy.Symbol('N'),
                'N': 5
            }
            
            save_derivation_output(nested_path, test_data)
            
            assert os.path.exists(nested_path), "File should be created in nested directory"

class TestIntegration:
    """Integration tests for the variance scaling module."""

    def test_end_to_end_derivation(self):
        """Test the full derivation pipeline."""
        # Step 1: Derive general expression
        general_expr = derive_variance_accumulation()
        assert isinstance(general_expr, sympy.Expr)
        
        # Step 2: Verify properties
        is_valid, message = verify_symmetry_and_linearity(general_expr)
        assert is_valid, "General expression should be valid"
        
        # Step 3: Derive for specific N
        specific_result = derive_variance_accumulation(N=20)
        assert isinstance(specific_result, dict)
        assert specific_result['N'] == 20
        
        # Step 4: Save output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'derivation.json')
            save_derivation_output(output_path, specific_result)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['N'] == 20
            assert 'expr' in loaded