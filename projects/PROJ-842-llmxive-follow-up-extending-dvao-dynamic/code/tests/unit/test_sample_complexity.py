"""
Unit tests for the Sample Complexity Derivation module.
"""

import pytest
import sympy
import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.derivation.sample_complexity import (
    invert_variance_to_sample_complexity,
    derive_sample_complexity_bound,
    verify_inversion_logic,
    save_derivation_output
)


class TestInversionLogic:
    """Tests for the core inversion logic."""

    def test_invert_simple_linear(self):
        """Test inversion of a simple linear variance equation: Var = (N * e) / M."""
        N = sympy.Symbol('N', positive=True)
        M = sympy.Symbol('M', positive=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        target = sympy.Symbol('target', positive=True)

        # Construct Var = (N * epsilon) / M
        variance_expr = (N * epsilon) / M

        solution = invert_variance_to_sample_complexity(
            variance_expr, target, M, N, epsilon
        )

        # Expected solution: M = (N * epsilon) / target
        expected = (N * epsilon) / target
        
        assert sympy.simplify(solution - expected) == 0

    def test_invert_complex_expression(self):
        """Test inversion with a slightly more complex expression."""
        N = sympy.Symbol('N', positive=True)
        M = sympy.Symbol('M', positive=True)
        epsilon = sympy.Symbol('epsilon', positive=True)
        target = sympy.Symbol('target', positive=True)
        rho = sympy.Symbol('rho', positive=True)

        # Var = (N * epsilon * (1 + rho)) / M
        variance_expr = (N * epsilon * (1 + rho)) / M

        solution = invert_variance_to_sample_complexity(
            variance_expr, target, M, N, epsilon
        )

        expected = (N * epsilon * (1 + rho)) / target
        assert sympy.simplify(solution - expected) == 0


class TestDeriveSampleComplexityBound:
    """Tests for the high-level derivation function."""

    def test_derive_returns_structure(self):
        """Test that derive_sample_complexity_bound returns the expected keys."""
        result = derive_sample_complexity_bound()
        
        assert "closed_form_equation_latex" in result
        assert "closed_form_equation_plain" in result
        assert "assumptions" in result
        assert isinstance(result["assumptions"], list)
        assert len(result["assumptions"]) > 0

    def test_derive_with_numeric_values(self):
        """Test derivation with specific numeric inputs."""
        result = derive_sample_complexity_bound(
            n_objectives_val=10,
            noise_var_val=0.5,
            target_variance_val=0.1
        )

        assert "evaluated_bound" in result
        assert isinstance(result["evaluated_bound"], float)
        # Check that the value is positive
        assert result["evaluated_bound"] > 0

    def test_derive_assumptions_inclusion(self):
        """Test that assumptions are explicitly listed."""
        result = derive_sample_complexity_bound()
        
        # Check for key assumptions mentioned in the docstring
        assumption_text = " ".join(result["assumptions"]).lower()
        assert "i.i.d." in assumption_text or "independent" in assumption_text
        assert "sample" in assumption_text or "1/m" in assumption_text


class TestVerification:
    """Tests for the verification logic."""

    def test_verify_inversion_logic(self):
        """Test that the verification function returns True for valid logic."""
        assert verify_inversion_logic() is True


class TestSaveDerivationOutput:
    """Tests for the file I/O functionality."""

    def test_save_creates_file(self):
        """Test that save_derivation_output creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            
            result = save_derivation_output(output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert "closed_form_equation_latex" in loaded
            assert "timestamp" in loaded
            assert loaded["verification_passed"] is True

    def test_save_directory_creation(self):
        """Test that save_derivation_output creates directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "nested", "dir")
            output_path = os.path.join(subdir, "test.json")
            
            # Should not raise
            save_derivation_output(output_path)
            
            assert os.path.exists(output_path)
