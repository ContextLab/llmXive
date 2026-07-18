import pytest
import sympy
import sys
import os
import json
import tempfile
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.derivation.variance_scaling import (
    derive_variance_accumulation,
    verify_symmetry_and_linearity,
    save_derivation_output
)

class TestVarianceScalingDerivation:
    """Test suite for variance scaling derivation with assumption logging."""

    def test_derive_variance_accumulation_returns_dict(self):
        """Test that derive_variance_accumulation returns a dictionary with required keys."""
        result = derive_variance_accumulation(N=5)
        
        assert isinstance(result, dict)
        assert 'expression' in result
        assert 'latex' in result
        assert 'assumptions' in result
        assert 'parameters' in result
        assert 'timestamp' in result

    def test_derive_variance_accumulation_includes_iid_assumption(self):
        """Test that the derivation explicitly logs i.i.d. noise assumption."""
        result = derive_variance_accumulation(N=10)
        
        assumptions = result['assumptions']
        assert len(assumptions) > 0
        
        # Check for i.i.d. assumption
        iid_found = any('independent and identically distributed' in str(ass).lower() 
                      for ass in assumptions)
        assert iid_found, "i.i.d. noise assumption must be explicitly logged"

    def test_derive_variance_accumulation_correct_expression(self):
        """Test that the derived expression is N * sigma_sq for i.i.d. noise."""
        N = 5
        result = derive_variance_accumulation(N=N)
        
        # Parse the expression
        sigma_sq = sympy.Symbol('sigma_sq', real=True, positive=True)
        expr = sympy.sympify(result['expression'])
        
        # Expected: N * sigma_sq
        expected = N * sigma_sq
        
        assert sympy.simplify(expr - expected) == 0

    def test_derive_variance_accumulation_parameters(self):
        """Test that parameters are correctly captured."""
        N = 20
        result = derive_variance_accumulation(N=N)
        
        assert result['parameters']['N'] == N
        assert result['parameters']['sigma_sq'] == 'σ²'

    def test_verify_symmetry_and_linearity(self):
        """Test symmetry and linearity verification."""
        result = verify_symmetry_and_linearity(N=10)
        
        assert 'linearity_verified' in result
        assert 'symmetry_verified' in result
        assert result['linearity_verified'] is True
        assert result['symmetry_verified'] is True

    def test_save_derivation_output(self):
        """Test saving derivation output to JSON file."""
        result = derive_variance_accumulation(N=5)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            save_derivation_output(result, filepath)
            
            # Verify file exists and is valid JSON
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['expression'] == result['expression']
            assert loaded['assumptions'] == result['assumptions']
        finally:
            os.unlink(filepath)

    def test_multiple_n_values(self):
        """Test derivation for multiple N values."""
        N_values = [5, 10, 20, 50]
        
        for N in N_values:
            result = derive_variance_accumulation(N=N)
            
            # Check expression is N * sigma_sq
            sigma_sq = sympy.Symbol('sigma_sq', real=True, positive=True)
            expr = sympy.sympify(result['expression'])
            expected = N * sigma_sq
            
            assert sympy.simplify(expr - expected) == 0
            
            # Check i.i.d. assumption is logged
            assert any('independent and identically distributed' in str(ass).lower() 
                     for ass in result['assumptions'])

    def test_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        result = derive_variance_accumulation(N=5)
        
        # Should not raise an exception
        datetime.fromisoformat(result['timestamp'])
        
        # Should be recent (within last minute)
        now = datetime.now()
        ts = datetime.fromisoformat(result['timestamp'])
        assert abs((now - ts).total_seconds()) < 60

class TestAssumptionLogging:
    """Specific tests for assumption logging functionality."""

    def test_all_required_assumptions_present(self):
        """Test that all required assumptions are explicitly logged."""
        result = derive_variance_accumulation(N=10)
        assumptions = result['assumptions']
        
        required_assumptions = [
            "independent and identically distributed",
            "Var(ε_i) = σ²",
            "Cov(ε_i, ε_j) = 0"
        ]
        
        for required in required_assumptions:
            found = any(required.lower() in str(ass).lower() for ass in assumptions)
            assert found, f"Required assumption '{required}' not found in logged assumptions"

    def test_assumption_clarity(self):
        """Test that assumptions are clearly stated and not ambiguous."""
        result = derive_variance_accumulation(N=5)
        assumptions = result['assumptions']
        
        # Each assumption should be a non-empty string
        for ass in assumptions:
            assert isinstance(ass, str)
            assert len(ass) > 10, f"Assumption too short: {ass}"
            
            # Should not contain placeholders or TODOs
            assert 'TODO' not in ass
            assert 'FIXME' not in ass
            assert '...' not in ass or '...' in ass and len(ass) > 20

    def test_assumptions_consistent_across_n(self):
        """Test that assumptions are consistent regardless of N value."""
        results = [derive_variance_accumulation(N=N) for N in [5, 10, 20]]
        
        # All should have the same number of assumptions
        n_assumptions = len(results[0]['assumptions'])
        for result in results:
            assert len(result['assumptions']) == n_assumptions
        
        # All should contain the same core assumptions
        for i in range(n_assumptions):
            for result in results:
                assert result['assumptions'][i] == results[0]['assumptions'][i]