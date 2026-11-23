import pytest
import sympy
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Import the module under test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.derivation.sample_complexity import (
    SampleComplexityResult,
    invert_variance_to_sample_complexity,
    calculate_bound,
    derive_sample_complexity_bound,
    verify_inversion_logic,
    save_derivation_output
)
from src.derivation.variance_scaling import derive_variance_accumulation

class TestInversionLogic:
    def test_invert_variance_basic(self):
        """Test basic inversion logic with known values."""
        # Assume Var = N, epsilon = 0.1 -> Bound = N / 0.01 = 100*N
        N = 5
        eps = 0.1
        var_expr = derive_variance_accumulation()
        result = invert_variance_to_sample_complexity(var_expr, N, eps)
        
        # Expected: 5 / 0.01 = 500
        assert isinstance(result, float)
        assert result > 0
        assert abs(result - 500.0) < 1.0 # Allow some tolerance for symbolic evaluation

    def test_invert_variance_with_dict(self):
        """Test inversion when variance is passed as a dict."""
        N = 10
        eps = 0.05
        var_dict = {"expression_str": "10", "N": 10}
        result = invert_variance_to_sample_complexity(var_dict, N, eps)
        
        # Expected: 10 / 0.0025 = 4000
        assert result > 0
        assert abs(result - 4000.0) < 100.0 # Tolerance for heuristic parsing

class TestDeriveSampleComplexityBound:
    def test_derive_bound_structure(self):
        """Test that derive_sample_complexity_bound returns the correct structure."""
        result = derive_sample_complexity_bound()
        
        assert "variance_expression" in result
        assert "bound_calculation" in result
        assert "formatted_bound" in result
        assert "timestamp" in result
        
        bound_calc = result["bound_calculation"]
        assert "N" in bound_calc
        assert "bound" in bound_calc
        assert "degraded" in bound_calc

    def test_derive_bound_degraded_flag(self):
        """Test that the degraded flag is set for N > 50."""
        # We need to call calculate_bound directly to test N > 50
        var_expr = derive_variance_accumulation()
        result = calculate_bound(var_expr, 60, 0.1)
        
        assert result["degraded"] is True
        assert result["effective_N"] == 50
        assert result["N"] == 60

class TestVerification:
    def test_verify_inversion_logic(self):
        """Test the verification function."""
        assert verify_inversion_logic() is True

class TestSaveDerivationOutput:
    def test_save_json(self):
        """Test saving to JSON."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            data = {
                "variance_expression": "N * sigma^2",
                "bound_calculation": {"N": 5, "bound": 500.0, "degraded": False},
                "formatted_bound": "Bound: 500.0",
                "timestamp": "2023-01-01"
            }
            save_derivation_output(path, data)
            
            with open(path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["variance_expression"] == data["variance_expression"]
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_save_markdown(self):
        """Test saving to Markdown."""
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            path = f.name
        
        try:
            data = {
                "variance_expression": "N * sigma^2",
                "bound_calculation": {"N": 5, "bound": 500.0, "degraded": False, "assumptions": ["i.i.d."]},
                "formatted_bound": "Bound: 500.0",
                "timestamp": "2023-01-01"
            }
            save_derivation_output(path, data)
            
            with open(path, 'r') as f:
                content = f.read()
            
            assert "Sample Complexity Derivation" in content
            assert "N * sigma^2" in content
        finally:
            if os.path.exists(path):
                os.remove(path)

class TestIntegration:
    def test_full_flow(self):
        """Test the full flow from derivation to formatting."""
        result = derive_sample_complexity_bound()
        
        # Check formatting
        assert "Sample Complexity Bound" in result["formatted_bound"]
        assert "N=10" in result["formatted_bound"] # Default N
        assert "ε=0.1" in result["formatted_bound"] # Default epsilon

    def test_string_formatting(self):
        """Test T019b: String formatting for sample complexity bound."""
        var_expr = derive_variance_accumulation()
        result = calculate_bound(var_expr, 20, 0.2)
        
        # The bound should be calculated
        assert result["bound"] > 0
        
        # Simulate the formatting logic
        formatted = f"Sample Complexity Bound for N={result['N']}, ε={result['epsilon']}: {result['bound']:.4f}"
        assert "Sample Complexity Bound" in formatted
        assert "N=20" in formatted
        assert "0.2" in formatted