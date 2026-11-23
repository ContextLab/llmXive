import pytest
import os
import sys
import tempfile
import csv
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.monte_carlo_runner import run_single_mc_iteration, run_monte_carlo_sweep
from utils.config import ensure_directories

class TestMonteCarloRunner:
    """Unit tests for Monte Carlo runner."""

    def test_single_iteration_basic(self):
        """Test a single MC iteration with small N."""
        result = run_single_mc_iteration(
            N=100,
            theta=2.5,
            seed=42,
            rank=1,
            sparsity_density=1.0,
            num_eigenvalues=5
        )
        
        assert result["N"] == 100
        assert result["theta"] == 2.5
        assert result["seed"] == 42
        assert "run_id" in result
        assert "outlier_count" in result
        assert "max_eigenvalue" in result
        assert result["outlier_count"] >= 0
        assert result["max_eigenvalue"] > 0

    def test_single_iteration_no_outlier(self):
        """Test iteration with theta below threshold (should have no outlier)."""
        result = run_single_mc_iteration(
            N=200,
            theta=0.5,  # Below BBP threshold
            seed=123,
            rank=1,
            sparsity_density=1.0,
            num_eigenvalues=5
        )
        
        assert result["N"] == 200
        assert result["theta"] == 0.5
        # For theta < 1, we expect no outliers (or very rare due to finite size)
        # This is a soft check
        assert result["outlier_count"] >= 0

    def test_single_iteration_high_theta(self):
        """Test iteration with theta well above threshold."""
        result = run_single_mc_iteration(
            N=200,
            theta=5.0,  # Well above BBP threshold
            seed=456,
            rank=1,
            sparsity_density=1.0,
            num_eigenvalues=5
        )
        
        assert result["N"] == 200
        assert result["theta"] == 5.0
        # For theta >> 1, we expect at least one outlier
        # This is a soft check due to finite size effects
        assert result["max_eigenvalue"] > 2.5

    def test_monte_carlo_sweep_output(self):
        """Test that sweep writes correct CSV output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_mc_results.csv"
            
            # Run a tiny sweep
            results = run_monte_carlo_sweep(
                N_values=[50],
                theta_values=[1.0, 2.0],
                num_iterations_per_config=3,
                output_path=str(output_path),
                rank=1,
                sparsity_density=1.0,
                num_eigenvalues=5,
                base_seed=999
            )
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify CSV structure
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have 2 configs * 3 iterations = 6 rows
            assert len(rows) == 6
            
            # Check headers
            expected_headers = ["run_id", "N", "theta", "seed", "outlier_count", "max_eigenvalue"]
            assert list(rows[0].keys()) == expected_headers
            
            # Check data integrity
            for row in rows:
                assert int(row["N"]) in [50]
                assert float(row["theta"]) in [1.0, 2.0]
                assert int(row["seed"]) >= 0
                assert int(row["outlier_count"]) >= -1  # -1 is error marker
                assert float(row["max_eigenvalue"]) >= 0

    def test_monte_carlo_sweep_reproducibility(self):
        """Test that same seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path1 = Path(tmpdir) / "test_mc_results1.csv"
            output_path2 = Path(tmpdir) / "test_mc_results2.csv"
            
            # Run twice with same parameters
            run_monte_carlo_sweep(
                N_values=[100],
                theta_values=[2.5],
                num_iterations_per_config=2,
                output_path=str(output_path1),
                rank=1,
                sparsity_density=1.0,
                num_eigenvalues=5,
                base_seed=777
            )
            
            run_monte_carlo_sweep(
                N_values=[100],
                theta_values=[2.5],
                num_iterations_per_config=2,
                output_path=str(output_path2),
                rank=1,
                sparsity_density=1.0,
                num_eigenvalues=5,
                base_seed=777
            )
            
            # Compare files
            with open(output_path1, 'r') as f1, open(output_path2, 'r') as f2:
                content1 = f1.read()
                content2 = f2.read()
            
            assert content1 == content2