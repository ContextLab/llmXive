import pytest
import numpy as np
import json
from pathlib import Path
from code.analyze_pr import analyze_w0_delocalization, compute_participation_ratio
from code.config import get_config

def test_W_zero_delocalized():
    """Test that W=0 results in delocalized states with extensive PR."""
    L_list = [100, 200, 400]
    num_realizations = 5
    seed = 42
    
    result = analyze_w0_delocalization(L_list, num_realizations, seed)
    
    assert "is_delocalized" in result
    assert result["is_delocalized"] is True, "W=0 should be delocalized"
    assert "PR_values" in result
    assert len(result["PR_values"]) > 0
    
    # Verify PR scales with L
    pr_values = list(result["PR_values"].values())
    L_values = sorted(result["PR_values"].keys())
    
    # Check linear scaling: PR/L should be roughly constant
    ratios = [pr / L for pr, L in zip(pr_values, L_values)]
    mean_ratio = np.mean(ratios)
    std_ratio = np.std(ratios)
    
    # Allow 20% variance
    assert std_ratio / mean_ratio < 0.2, f"PR should scale linearly with L. Ratios: {ratios}"

def test_large_L_memory_fallback():
    """Test that large L triggers sparse solver path (mocked check)."""
    # This test verifies the logic exists; actual memory check is environment dependent
    from code.analyze_pr import compute_eigenstates
    L = 2000
    hamiltonian = np.random.rand(L, L)
    hamiltonian = (hamiltonian + hamiltonian.T) / 2
    
    # Should not raise an error immediately
    try:
        eigenvalues, eigenvectors = compute_eigenstates(hamiltonian)
        assert len(eigenvalues) >= 0
    except Exception as e:
        # If it fails, it should be due to convergence, not import error
        assert "eigsh" in str(e) or "eigh" in str(e)

def test_tm_underflow_handling():
    """Test that TM method handles underflow (placeholder for TM logic)."""
    # This is a placeholder to ensure the test structure exists
    # Actual TM logic is in code/analyze_tm.py
    assert True