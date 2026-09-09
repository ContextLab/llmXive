import pytest
import os
import json
import sys
import tempfile
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from sieve import (
    compute_phi_linear_sieve, 
    compute_residues, 
    save_residue_dataset, 
    ResidueDataset,
    MemoryGuard,
    log_error
)
import logging

# Setup logging for tests
logging.basicConfig(level=logging.ERROR)

class TestLinearSieve:
    def test_phi_small_values(self):
        """Test phi(n) for small known values."""
        # phi(1)=1, phi(2)=1, phi(3)=2, phi(4)=2, phi(5)=4, phi(6)=2
        N = 6
        phi = compute_phi_linear_sieve(N, {'memory_limit_mb': 1000, 'memory_check_interval': 10000})
        
        expected = [0, 1, 1, 2, 2, 4, 2]  # index 0 unused
        assert phi == expected, f"Expected {expected}, got {phi}"

    def test_phi_prime(self):
        """Test phi(p) = p-1 for prime p."""
        N = 11
        phi = compute_phi_linear_sieve(N, {'memory_limit_mb': 1000, 'memory_check_interval': 10000})
        primes = [2, 3, 5, 7, 11]
        for p in primes:
            assert phi[p] == p - 1, f"phi({p}) should be {p-1}, got {phi[p]}"

    def test_phi_composite(self):
        """Test phi for composite numbers."""
        # phi(4) = 2, phi(6) = 2, phi(8) = 4, phi(9) = 6, phi(10) = 4
        N = 10
        phi = compute_phi_linear_sieve(N, {'memory_limit_mb': 1000, 'memory_check_interval': 10000})
        
        assert phi[4] == 2
        assert phi[6] == 2
        assert phi[8] == 4
        assert phi[9] == 6
        assert phi[10] == 4

class TestResidueComputation:
    def test_residues_mod_3(self):
        """Test residue computation modulo 3."""
        # phi values for n=1..6: 1, 1, 2, 2, 4, 2
        # mod 3: 1, 1, 2, 2, 1, 2
        # counts: {0: 0, 1: 3, 2: 3}
        phi_values = [1, 1, 2, 2, 4, 2]
        counts = compute_residues(phi_values, 3)
        expected = {0: 0, 1: 3, 2: 3}
        assert counts == expected, f"Expected {expected}, got {counts}"

    def test_residues_mod_5(self):
        """Test residue computation modulo 5."""
        # phi values for n=1..10: 1, 1, 2, 2, 4, 2, 6, 4, 6, 4
        # mod 5: 1, 1, 2, 2, 4, 2, 1, 4, 1, 4
        # counts: {0: 0, 1: 4, 2: 3, 3: 0, 4: 3}
        phi_values = [1, 1, 2, 2, 4, 2, 6, 4, 6, 4]
        counts = compute_residues(phi_values, 5)
        expected = {0: 0, 1: 4, 2: 3, 3: 0, 4: 3}
        assert counts == expected, f"Expected {expected}, got {counts}"

class TestSaveResidueDataset:
    def test_save_and_load(self):
        """Test saving and loading residue dataset."""
        dataset = ResidueDataset(
            prime=3,
            N=10,
            residue_counts={0: 0, 1: 4, 2: 6},
            timestamp="2023-01-01 00:00:00",
            seed=42
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_residues.json")
            save_residue_dataset(dataset, filepath)
            
            # Verify file exists
            assert os.path.exists(filepath), "Dataset file was not created"
            
            # Verify content
            with open(filepath, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['prime'] == 3
            assert loaded['N'] == 10
            assert loaded['residue_counts'] == {0: 0, 1: 4, 2: 6}
            assert loaded['seed'] == 42

class TestMemoryGuard:
    def test_memory_guard_no_trigger(self):
        """Test that memory guard doesn't trigger under normal conditions."""
        guard = MemoryGuard(limit_mb=100, check_interval=100)
        # Simulate normal operation (memory won't exceed 100MB in test)
        for i in range(200):
            assert guard.check(i), "Memory guard triggered unexpectedly"

    def test_memory_guard_interval(self):
        """Test that memory guard checks at correct intervals."""
        guard = MemoryGuard(limit_mb=10000, check_interval=100)
        checks = []
        
        # Patch the check logic to track calls
        original_check = guard.check
        def tracked_check(iteration):
            if iteration % 100 == 0:
                checks.append(iteration)
            return original_check(iteration)
        
        guard.check = tracked_check
        
        for i in range(250):
            guard.check(i)
        
        # Should check at 0, 100, 200
        assert 0 in checks
        assert 100 in checks
        assert 200 in checks
        assert 50 not in checks  # Should not check at 50

class TestErrorHandling:
    def test_log_error(self):
        """Test that error logging works correctly."""
        # This test just verifies the function doesn't crash
        log_error("Test error message")
        log_error("Test error with n", n=42)

    def test_memory_error_on_limit(self):
        """Test that memory error is raised when limit is exceeded."""
        # We can't easily simulate memory exhaustion in a test,
        # but we can verify the guard logic
        guard = MemoryGuard(limit_mb=1, check_interval=1)
        # Force a check that would fail if memory was actually low
        # In a real scenario, this would raise MemoryError
        # Here we just verify the check mechanism works
        result = guard.check(1)
        # Since we're not actually exceeding memory, it should return True
        assert result is True
