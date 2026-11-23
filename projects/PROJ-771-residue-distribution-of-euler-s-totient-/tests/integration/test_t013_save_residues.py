import os
import json
import tempfile
import pytest
from sieve import ResidueDataset, save_residue_dataset, load_residue_dataset, compute_phi_linear_sieve, compute_residues, MemoryGuard

class TestT013Integration:
    """Integration test for T013: Save raw residue counts to JSON."""

    def test_full_pipeline_save_residues(self):
        """Test the full pipeline: compute phi, compute residues, save to JSON."""
        N = 100
        prime = 5
        seed = 42
        memory_limit_mb = 6000
        check_interval = 10000

        # Setup memory guard
        memory_guard = MemoryGuard(memory_limit_mb, check_interval)

        # Compute phi values
        phi_values = compute_phi_linear_sieve(N, memory_guard)

        # Compute residues
        residue_counts = compute_residues(phi_values, prime)

        # Create dataset
        dataset = ResidueDataset(
            prime=prime,
            N=N,
            residue_counts=residue_counts,
            seed=seed
        )

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_residue_dataset(dataset, temp_path)

            # Verify file exists and is valid JSON
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)

            # Verify content
            assert saved_data['prime'] == prime
            assert saved_data['N'] == N
            assert saved_data['residue_counts'] == residue_counts
            assert saved_data['seed'] == seed
            
            # Verify sum of counts equals N-1 (since we start from n=1)
            total_count = sum(residue_counts.values())
            assert total_count == N - 1  # phi(1) to phi(N), so N-1 values

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_multiple_primes_save(self):
        """Test saving residue data for multiple primes."""
        N = 50
        primes = [3, 5, 7]
        memory_guard = MemoryGuard(6000, 10000)

        phi_values = compute_phi_linear_sieve(N, memory_guard)

        with tempfile.TemporaryDirectory() as tmpdir:
            for prime in primes:
                residue_counts = compute_residues(phi_values, prime)
                dataset = ResidueDataset(
                    prime=prime,
                    N=N,
                    residue_counts=residue_counts
                )
                
                output_path = os.path.join(tmpdir, f"residues_{prime}_{N}.json")
                save_residue_dataset(dataset, output_path)
                
                # Verify each file
                assert os.path.exists(output_path)
                with open(output_path, 'r') as f:
                    data = json.load(f)
                assert data['prime'] == prime
                assert data['N'] == N

    def test_large_n_save(self):
        """Test saving residue data for a larger N (performance check)."""
        N = 10000
        prime = 11
        memory_guard = MemoryGuard(6000, 10000)

        phi_values = compute_phi_linear_sieve(N, memory_guard)
        residue_counts = compute_residues(phi_values, prime)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            dataset = ResidueDataset(
                prime=prime,
                N=N,
                residue_counts=residue_counts
            )
            save_residue_dataset(dataset, temp_path)

            assert os.path.exists(temp_path)
            
            # Verify file size is reasonable (not empty, not huge)
            file_size = os.path.getsize(temp_path)
            assert file_size > 0
            assert file_size < 10 * 1024 * 1024  # Less than 10MB

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)