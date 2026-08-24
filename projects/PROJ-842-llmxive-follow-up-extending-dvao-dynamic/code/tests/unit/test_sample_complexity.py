import pytest
import sympy
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.derivation.sample_complexity import (
    invert_variance_to_sample_complexity,
    derive_sample_complexity_bound,
    verify_inversion_logic,
    save_derivation_output,
    calculate_bound,
    SampleComplexityResult
)
from src.derivation.variance_scaling import derive_variance_accumulation

class TestInversionLogic:
    """Tests for the inversion logic (variance -> sample complexity)."""
    
    def test_invert_variance_basic(self):
        """Test basic inversion of variance expression."""
        variance_expr = derive_variance_accumulation()
        result = invert_variance_to_sample_complexity(variance_expr, 0.01)
        
        # For N * sigma^2 = 0.01, if sigma^2 = 0.01, then N = 1
        # The result should be a sympy expression
        assert isinstance(result, sympy.Expr)
    
    def test_invert_variance_with_values(self):
        """Test inversion with specific values."""
        variance_expr = derive_variance_accumulation()
        target_var = 0.25
        result = invert_variance_to_sample_complexity(variance_expr, target_var)
        
        # Should solve for N
        assert result is not None

class TestDeriveSampleComplexityBound:
    """Tests for the sample complexity bound derivation."""
    
    def test_derive_sample_complexity_bound(self):
        """Test the main derivation function."""
        result = derive_sample_complexity_bound()
        
        assert "variance_expression" in result
        assert "is_valid" in result
        assert "results" in result
        assert len(result["results"]) > 0
        
        # Check that is_valid is True
        assert result["is_valid"] is True
    
    def test_derive_sample_complexity_bound_structure(self):
        """Test the structure of the derivation result."""
        result = derive_sample_complexity_bound()
        
        for res in result["results"]:
            assert "N" in res
            assert "effective_N" in res
            assert "epsilon" in res
            assert "bound" in res
            assert "degraded" in res
            assert "formula" in res
            assert "assumptions" in res

class TestVerification:
    """Tests for the verification logic."""
    
    def test_verify_inversion_logic(self):
        """Test the inversion logic verification."""
        is_valid = verify_inversion_logic()
        assert is_valid is True

class TestSaveDerivationOutput:
    """Tests for saving derivation output."""
    
    def test_save_derivation_output(self):
        """Test saving derivation output to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            
            test_data = {
                "test": "data",
                "number": 42
            }
            
            save_derivation_output(test_data, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data

class TestIntegration:
    """Integration tests for the sample complexity module."""
    
    def test_calculate_bound_basic(self):
        """Test basic bound calculation."""
        variance_expr = derive_variance_accumulation()
        result = calculate_bound(variance_expr, N=5, epsilon=0.1)
        
        assert isinstance(result, SampleComplexityResult)
        assert result.N == 5
        assert result.epsilon == 0.1
        assert result.degraded is False
        assert result.effective_N == 5
        # Expected bound: (5 * 0.1^2) / 0.1^2 = 5
        assert abs(result.bound - 5.0) < 1e-6
    
    def test_calculate_bound_degraded(self):
        """Test bound calculation with N > 50 (degraded mode)."""
        variance_expr = derive_variance_accumulation()
        result = calculate_bound(variance_expr, N=60, epsilon=0.1)
        
        assert isinstance(result, SampleComplexityResult)
        assert result.N == 60
        assert result.degraded is True
        assert result.effective_N == 50
        # Effective N is 50, so bound = (50 * 0.1^2) / 0.1^2 = 50
        assert abs(result.bound - 50.0) < 1e-6
    
    def test_calculate_bound_various_epsilon(self):
        """Test bound calculation with various epsilon values."""
        variance_expr = derive_variance_accumulation()
        
        for epsilon in [0.1, 0.2, 0.5]:
            result = calculate_bound(variance_expr, N=10, epsilon=epsilon)
            assert result.N == 10
            assert result.epsilon == epsilon
            assert result.degraded is False
            # Bound should be N * sigma^2 / epsilon^2 = 10 * epsilon^2 / epsilon^2 = 10
            assert abs(result.bound - 10.0) < 1e-6
    
    def test_calculate_bound_edge_case_zero_epsilon(self):
        """Test that zero epsilon raises an error."""
        variance_expr = derive_variance_accumulation()
        
        with pytest.raises(ValueError, match="Epsilon cannot be zero"):
            calculate_bound(variance_expr, N=5, epsilon=0.0)
    
    def test_sample_complexity_result_defaults(self):
        """Test default values for SampleComplexityResult."""
        result = SampleComplexityResult(
            bound=10.0,
            N=5,
            epsilon=0.1
        )
        
        assert result.degraded is False
        assert result.effective_N is None
        assert result.formula == ""
        assert result.assumptions is not None
        assert "i.i.d. noise" in result.assumptions
    
    def test_sample_complexity_result_with_degraded(self):
        """Test SampleComplexityResult with degraded mode."""
        result = SampleComplexityResult(
            bound=50.0,
            N=60,
            epsilon=0.1,
            degraded=True,
            effective_N=50,
            formula="M >= 50",
            assumptions=["test assumption"]
        )
        
        assert result.degraded is True
        assert result.effective_N == 50
        assert result.formula == "M >= 50"
        assert result.assumptions == ["test assumption"]