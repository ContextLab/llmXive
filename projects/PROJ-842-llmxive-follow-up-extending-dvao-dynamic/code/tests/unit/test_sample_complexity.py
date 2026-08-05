import pytest
import sympy
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Import the functions under test from the derivation module
from src.derivation.sample_complexity import (
    invert_variance_to_sample_complexity,
    derive_sample_complexity_bound,
    verify_inversion_logic,
    save_derivation_output
)
from src.derivation.variance_scaling import derive_variance_accumulation

class TestInversionLogic:
    """Tests for the inversion logic of variance to sample complexity."""

    def test_invert_variance_basic(self):
        """Test basic inversion of variance expression to sample complexity."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        
        # Create a simple variance expression: N * epsilon^2
        variance_expr = N * epsilon**2
        
        # Invert to get sample complexity
        result = invert_variance_to_sample_complexity(variance_expr, N, epsilon)
        
        # The sample complexity should be related to N * epsilon^2
        # For variance = N * epsilon^2, sample_complexity ~ 1 / (epsilon^2) * N
        assert result is not None
        assert isinstance(result, sympy.Expr)

    def test_invert_variance_with_constants(self):
        """Test inversion with constant factors."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        c = sympy.Symbol('c', positive=True)
        
        variance_expr = c * N * epsilon**2
        result = invert_variance_to_sample_complexity(variance_expr, N, epsilon)
        
        assert result is not None
        assert isinstance(result, sympy.Expr)

    def test_invert_variance_linear_case(self):
        """Test inversion for linear variance scaling."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        
        # Linear variance: Var = N * sigma^2
        variance_expr = N * epsilon**2
        
        result = invert_variance_to_sample_complexity(variance_expr, N, epsilon)
        
        assert result is not None

class TestDeriveSampleComplexityBound:
    """Tests for the sample complexity bound derivation."""

    def test_derive_bound_returns_dict(self):
        """Test that derive_sample_complexity_bound returns a dictionary."""
        result = derive_sample_complexity_bound()
        
        assert isinstance(result, dict)
        assert 'bound' in result
        assert 'N' in result
        assert 'epsilon' in result

    def test_derive_bound_with_N_5(self):
        """Test derivation with N=5."""
        with patch('src.derivation.sample_complexity.derive_variance_accumulation') as mock_var:
            # Mock the variance accumulation to return a simple expression
            N = sympy.Symbol('N', positive=True, integer=True)
            epsilon = sympy.Symbol('epsilon', positive=True)
            mock_var.return_value = {'expression': N * epsilon**2, 'N': 5, 'epsilon': epsilon}
            
            result = derive_sample_complexity_bound()
            
            assert result is not None
            assert isinstance(result, dict)

    def test_derive_bound_with_N_50(self):
        """Test derivation with N=50 (edge case)."""
        with patch('src.derivation.sample_complexity.derive_variance_accumulation') as mock_var:
            N = sympy.Symbol('N', positive=True, integer=True)
            epsilon = sympy.Symbol('epsilon', positive=True)
            mock_var.return_value = {'expression': N * epsilon**2, 'N': 50, 'epsilon': epsilon}
            
            result = derive_sample_complexity_bound()
            
            assert result is not None
            assert isinstance(result, dict)

class TestVerification:
    """Tests for the verification of inversion logic."""

    def test_verify_inversion_logic_basic(self):
        """Test basic verification of inversion logic."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        
        variance_expr = N * epsilon**2
        result = verify_inversion_logic(variance_expr, N, epsilon)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'verification_passed' in result

    def test_verify_inversion_with_simplify(self):
        """Test verification with sympy simplification."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        
        # Create a more complex expression that should simplify
        variance_expr = (N * epsilon**2) / epsilon
        
        result = verify_inversion_logic(variance_expr, N, epsilon)
        
        assert result is not None

    def test_verify_inversion_returns_true_for_valid_inversion(self):
        """Test that verification returns True for a valid inversion."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        
        variance_expr = N * epsilon**2
        result = verify_inversion_logic(variance_expr, N, epsilon)
        
        # The result should indicate successful verification
        assert result['verification_passed'] is True

class TestSaveDerivationOutput:
    """Tests for saving derivation output to file."""

    def test_save_derivation_output_creates_file(self):
        """Test that save_derivation_output creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            
            result_data = {
                'bound': 'N * epsilon^2',
                'N': 10,
                'epsilon': 0.1,
                'assumptions': ['i.i.d. noise']
            }
            
            save_derivation_output(result_data, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == result_data

    def test_save_derivation_output_with_sympy_expr(self):
        """Test saving with sympy expression (converted to string)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output_sympy.json")
            
            N = sympy.Symbol('N', positive=True, integer=True)
            epsilon = sympy.Symbol('epsilon', positive=True)
            
            result_data = {
                'bound': str(N * epsilon**2),
                'N': 20,
                'epsilon': str(epsilon),
                'expression': str(N * epsilon**2)
            }
            
            save_derivation_output(result_data, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data['bound'] == 'N*epsilon**2'

    def test_save_derivation_output_creates_directory_if_missing(self):
        """Test that save_derivation_output creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test_output.json")
            
            result_data = {'test': 'data'}
            
            # Should not raise an error
            save_derivation_output(result_data, output_path)
            
            assert os.path.exists(output_path)

class TestIntegration:
    """Integration tests for the sample complexity module."""

    def test_full_derivation_pipeline(self):
        """Test the full pipeline from variance derivation to sample complexity."""
        with patch('src.derivation.sample_complexity.derive_variance_accumulation') as mock_var:
            N = sympy.Symbol('N', positive=True, integer=True)
            epsilon = sympy.Symbol('epsilon', positive=True)
            
            # Mock the variance accumulation
            mock_var.return_value = {
                'expression': N * epsilon**2,
                'N': 10,
                'epsilon': epsilon
            }
            
            # Run the derivation
            result = derive_sample_complexity_bound()
            
            assert result is not None
            assert 'bound' in result
            assert result['N'] == 10

    def test_inversion_matches_derivation(self):
        """Test that the inversion logic is consistent with the derivation."""
        N = sympy.Symbol('N', positive=True, integer=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        
        variance_expr = N * epsilon**2
        
        # Invert
        sample_complexity = invert_variance_to_sample_complexity(variance_expr, N, epsilon)
        
        # Verify
        verification = verify_inversion_logic(variance_expr, N, epsilon)
        
        assert verification['verification_passed'] is True

    def test_derivation_with_different_N_values(self):
        """Test derivation with multiple N values."""
        for n_val in [5, 10, 20, 50]:
            with patch('src.derivation.sample_complexity.derive_variance_accumulation') as mock_var:
                N = sympy.Symbol('N', positive=True, integer=True)
                epsilon = sympy.Symbol('epsilon', positive=True)
                
                mock_var.return_value = {
                    'expression': N * epsilon**2,
                    'N': n_val,
                    'epsilon': epsilon
                }
                
                result = derive_sample_complexity_bound()
                
                assert result is not None
                assert result['N'] == n_val