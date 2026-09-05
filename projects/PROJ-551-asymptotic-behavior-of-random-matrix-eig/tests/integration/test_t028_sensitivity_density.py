"""
Integration test for Task T028: Sensitivity Density Sweep.
Verifies that the sweep script runs and produces the expected CSV output.
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sensitivity_density_sweep import run_sensitivity_density_sweep

def test_t028_sweep_execution():
    """
    Test that the sweep runs and produces a CSV with the expected structure.
    Uses a small N for speed in testing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sensitivity_test.csv"
        
        # Run a minimal sweep
        results = run_sensitivity_density_sweep(
            densities=[0.1, 0.2],
            patterns=["diagonal", "random-sparse"],
            N=100,  # Small N for test
            theta=2.5,
            base_seed=42,
            rank=1,
            tol=1e-10,
            output_path=output_path
        )

        # Assert file exists
        assert output_path.exists(), "Output CSV file was not created"

        # Assert content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, "CSV is empty"
        
        # Check columns
        expected_cols = [
            "density", "pattern", "theta", "N", "seed", "rank", "success",
            "outlier_detected", "max_eigenvalue", "bbp_threshold", "transition_candidate"
        ]
        for col in expected_cols:
            assert col in rows[0], f"Missing column: {col}"

        # Check values
        densities_found = set(float(r['density']) for r in rows)
        patterns_found = set(r['pattern'] for r in rows)
        
        assert 0.1 in densities_found
        assert 0.2 in densities_found
        assert "diagonal" in patterns_found
        assert "random-sparse" in patterns_found

        # Check that at least some runs succeeded
        successes = [r for r in rows if r['success'] == 'True']
        assert len(successes) > 0, "No successful runs in test"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])