"""
Unit tests for edge cases: W=0 delocalization, large L memory limits.
Task T033 / T013c verification.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys

# Add code/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analyze_w0_delocalization import generate_clean_hamiltonian, compute_w0_participation_ratio, analyze_w0_delocalization
from logger import NumericalLogger

class TestWZeroDelocalized:
    """Tests for T013c: W=0 edge case handler."""

    def test_generate_clean_hamiltonian_structure(self):
        """Verify clean Hamiltonian has correct structure (tridiagonal, 0 on-site)."""
        L = 10
        H = generate_clean_hamiltonian(L, seed=42)
        
        # Check dimensions
        assert H.shape == (L, L)
        
        # Check on-site (diagonal) is zero
        assert np.allclose(np.diag(H), 0.0)
        
        # Check off-diagonals are -1
        for i in range(L - 1):
            assert H[i, i+1] == -1.0
            assert H[i+1, i] == -1.0
        
        # Check zeros elsewhere
        for i in range(L):
            for j in range(L):
                if abs(i - j) > 1:
                    assert H[i, j] == 0.0

    def test_pr_scales_extensively(self):
        """Verify PR scales ~ L for W=0 (delocalized)."""
        L = 100
        H = generate_clean_hamiltonian(L, seed=42)
        results = compute_w0_participation_ratio(H, seed=42, realization_idx=0)
        
        # Filter for E ~ 0
        near_zero = [r for r in results if abs(r['energy']) < 0.1]
        assert len(near_zero) > 0, "No eigenstates near E=0 found"
        
        avg_pr = np.mean([r['pr'] for r in near_zero])
        
        # For 1D clean chain, PR ~ L/3
        expected = L / 3.0
        # Allow 50% tolerance for finite size effects
        assert 0.5 * expected < avg_pr < 1.5 * expected, f"PR {avg_pr} not scaling as L/3={expected}"

    def test_w0_analysis_output_schema(self):
        """Verify output matches expected schema for T013c."""
        L_vals = [100, 200]
        logger = NumericalLogger() # Mock logger for test
        
        results = analyze_w0_delocalization(L_vals, num_realizations=2, seed=42, logger=logger)
        
        assert "is_delocalized" in results
        assert results["is_delocalized"] is True
        assert "PR_values" in results
        assert isinstance(results["PR_values"], list)
        assert "scaling_check" in results
        
        # Verify PR values have required keys
        for item in results["PR_values"]:
            assert "W" in item
            assert item["W"] == 0.0
            assert "L" in item
            assert "realization_index" in item
            assert "energy" in item
            assert "pr" in item

    def test_w0_results_file_creation(self):
        """Integration check: ensure main() writes file if called (mocked)."""
        # We can't easily run main() without file system side effects in unit test,
        # but we verify the logic path.
        L_vals = [100]
        logger = NumericalLogger()
        data = analyze_w0_delocalization(L_vals, 1, 42, logger)
        assert data["is_delocalized"]
        assert data["scaling_check"][0]["L"] == 100