"""
Unit tests for T013c: W=0 Edge Case Handler.
"""
import json
import os
import sys
from pathlib import Path
import tempfile
import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analyze_w0_delocalization import generate_clean_hamiltonian, compute_w0_participation_ratio, analyze_w0_delocalization
from code.config import Config
from code.logger import NumericalLogger

def test_generate_clean_hamiltonian_structure():
    """Test that clean Hamiltonian has correct structure."""
    L = 10
    H = generate_clean_hamiltonian(L, seed=42)
    
    assert H.shape == (L, L)
    # Diagonal should be 0
    assert np.allclose(np.diag(H), 0)
    # Off-diagonals should be -1
    for i in range(L-1):
        assert H[i, i+1] == -1
        assert H[i+1, i] == -1

def test_clean_hamiltonian_eigenvalues():
    """Test eigenvalues of clean Hamiltonian (known analytic solution)."""
    L = 4
    H = generate_clean_hamiltonian(L, seed=42)
    eigenvalues = np.linalg.eigvalsh(H)
    
    # Analytic eigenvalues for 1D chain with open boundaries: -2*cos(k*pi/(L+1))
    # k = 1..L
    expected = [-2 * np.cos(k * np.pi / (L + 1)) for k in range(1, L + 1)]
    expected.sort()
    
    assert np.allclose(np.sort(eigenvalues), expected)

def test_w0_scaling_check():
    """Test that W=0 analysis correctly identifies extensive scaling."""
    # Mock config
    config = {
        "W_LIST": [0.0],
        "SEED": 42
    }
    
    # Mock logger
    logger = NumericalLogger(
        log_dir=Path("data/metadata"),
        seed=42,
        max_iterations=1000
    )
    
    results = analyze_w0_delocalization(config, logger)
    
    assert results["is_delocalized"] is True
    assert len(results["PR_values"]) >= 2  # At least 2 sizes
    
    # Check that PR scales with L
    pr_values = [r["avg_pr"] for r in results["PR_values"]]
    l_values = [r["L"] for r in results["PR_values"]]
    
    # PR should increase with L
    for i in range(1, len(pr_values)):
        assert pr_values[i] > pr_values[i-1], f"PR should increase with L: {pr_values[i-1]} -> {pr_values[i]}"
    
    # Check scaling ratios
    if len(results["scaling_check"]["observed_ratios"]) > 0:
        for ratio_info in results["scaling_check"]["observed_ratios"]:
            # For delocalized states, PR ~ L, so PR_ratio should be close to L_ratio
            assert ratio_info["matches_linear"] is True, f"Scaling mismatch: PR_ratio={ratio_info['pr_ratio']}, L_ratio={ratio_info['l_ratio']}"

def test_w0_output_file_schema():
    """Test that the output file matches the expected schema."""
    # This test assumes main() has been run and file exists
    output_path = Path("data/processed/w0_results.json")
    
    if not output_path.exists():
        pytest.skip("Output file not found. Run main() first.")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "is_delocalized" in data
    assert data["is_delocalized"] is True
    assert "PR_values" in data
    assert isinstance(data["PR_values"], list)
    
    for item in data["PR_values"]:
        assert "L" in item
        assert "avg_pr" in item
        assert isinstance(item["L"], int)
        assert isinstance(item["avg_pr"], float)
        
        # Sanity check: PR should be positive and <= L
        assert item["avg_pr"] > 0
        assert item["avg_pr"] <= item["L"]