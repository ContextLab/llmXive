"""
Unit tests for the linear sieve implementation in code/sieve.py.

This module verifies:
1. Correctness of compute_phi_linear_sieve against known mathematical values.
2. Correctness of compute_residues for small primes.
3. Integration with ResidueDataset and save/load functionality.
4. MemoryGuard trigger behavior under simulated memory pressure.
"""
import pytest
import os
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.sieve import (
    compute_phi_linear_sieve,
    compute_residues,
    ResidueDataset,
    save_residue_dataset,
    load_residue_dataset,
    MemoryGuard
)


# --- Known Values for Verification ---
# Euler's Totient Function phi(n) for n=1 to 20:
# n: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
# phi: 1, 1, 2, 2, 4, 2, 6, 4, 6, 4, 10, 4, 12, 6, 8, 8, 16, 6, 18, 8
KNOWN_PHI_VALUES = {
    1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 2, 7: 6, 8: 4, 9: 6, 10: 4,
    11: 10, 12: 4, 13: 12, 14: 6, 15: 8, 16: 8, 17: 16, 18: 6, 19: 18, 20: 8
}

def naive_phi(n):
    """Naive implementation of Euler's totient function for verification."""
    if n == 0:
        return 0
    result = n
    p = 2
    while p * p <= n:
        if n % p == 0:
            while n % p == 0:
                n //= p
            result -= result // p
        p += 1
    if n > 1:
        result -= result // n
    return result


def test_compute_phi_linear_sieve_small_values():
    """Test compute_phi_linear_sieve against known small values."""
    N = 20
    phi_values = compute_phi_linear_sieve(N)

    assert len(phi_values) == N + 1, f"Expected length {N+1}, got {len(phi_values)}"
    assert phi_values[0] == 0, "phi(0) should be 0"

    for n in range(1, N + 1):
        expected = KNOWN_PHI_VALUES[n]
        actual = phi_values[n]
        assert actual == expected, f"phi({n}) mismatch: expected {expected}, got {actual}"


def test_compute_phi_linear_sieve_matches_naive():
    """Test compute_phi_linear_sieve against a naive implementation for a larger range."""
    N = 500
    phi_values = compute_phi_linear_sieve(N)

    for n in range(1, N + 1):
        expected = naive_phi(n)
        actual = phi_values[n]
        assert actual == expected, f"phi({n}) mismatch: expected {expected}, got {actual}"


def test_compute_residues_consistency():
    """Test that compute_residues correctly aggregates phi values modulo p."""
    N = 50
    primes = [3, 5, 7]
    phi_values = compute_phi_linear_sieve(N)

    for p in primes:
        residues = compute_residues(phi_values, p)
        
        # Verify sum of counts equals N
        total_count = sum(residues.values())
        assert total_count == N, f"Sum of residues for p={p} is {total_count}, expected {N}"

        # Verify each count matches manual calculation
        manual_counts = {i: 0 for i in range(p)}
        for n in range(1, N + 1):
            r = phi_values[n] % p
            manual_counts[r] += 1

        assert residues == manual_counts, f"Residue counts mismatch for p={p}: expected {manual_counts}, got {residues}"


def test_residue_dataset_serialization(tmp_path):
    """Test saving and loading ResidueDataset."""
    N = 100
    primes = [3, 5]
    phi_values = compute_phi_linear_sieve(N)
    
    output_dir = tmp_path / "test_data"
    output_dir.mkdir()

    for p in primes:
        residues = compute_residues(phi_values, p)
        
        dataset = ResidueDataset(
            N=N,
            prime=p,
            residue_counts=residues,
            total_count=sum(residues.values())
        )
        
        file_path = output_dir / f"residues_{p}_{N}.json"
        save_residue_dataset(dataset, str(file_path))
        
        # Verify file exists and can be loaded
        assert file_path.exists(), f"Output file {file_path} was not created"
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert data['N'] == N
        assert data['prime'] == p
        assert data['total_count'] == N
        assert data['residue_counts'] == residues


def test_memory_guard_trigger():
    """
    Unit test for MemoryGuard trigger.
    Mocks psutil to simulate memory usage >= 90% and ensures MemoryGuard raises an error.
    """
    # Create a MemoryGuard instance with a low threshold for testing
    # We set the limit to 100MB for the test, and mock usage to 95MB (95%)
    guard = MemoryGuard(limit_mb=100)
    
    # Mock psutil.virtual_memory to return 95% usage
    mock_memory = MagicMock()
    mock_memory.percent = 95.0  # Above the 90% threshold
    
    with patch('code.sieve.psutil.virtual_memory', return_value=mock_memory):
        with pytest.raises(RuntimeError) as exc_info:
            guard.check_memory()
        
        assert "Memory usage" in str(exc_info.value)
        assert "exceeded limit" in str(exc_info.value)


def test_memory_guard_safe():
    """
    Unit test to ensure MemoryGuard does NOT trigger when usage is safe.
    """
    guard = MemoryGuard(limit_mb=100)
    
    # Mock psutil.virtual_memory to return 80% usage
    mock_memory = MagicMock()
    mock_memory.percent = 80.0
    
    with patch('code.sieve.psutil.virtual_memory', return_value=mock_memory):
        # Should not raise
        guard.check_memory()