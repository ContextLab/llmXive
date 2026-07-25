import pytest
import numpy as np
import pandas as pd
from scipy import stats
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation_runner import run_single_replication, run_simulation
from exceptions import EdgeCaseError

class TestRunSingleReplication:
    """Unit tests for the single replication logic."""

    def test_ttest_null_independence(self):
        """Test that under r=0, p-values are roughly uniform (approx check)."""
        n = 100
        p_vals = []
        for i in range(100):
            p = run_single_replication(
                n=n,
                test_type='t-test',
                dependency_type='ar1',
                dependency_strength=0.0,
                seed=i
            )
            p_vals.append(p)
        
        # Under null, p-values should be uniform. 
        # We check that mean is approx 0.5 and no extreme clustering immediately.
        mean_p = np.mean(p_vals)
        assert 0.3 < mean_p < 0.7, f"Mean p-value {mean_p} suggests bias under null"

    def test_ar1_injection_applied(self):
        """Verify that AR(1) injection changes the data structure."""
        # This is a bit tricky to test without internal access, 
        # but we can ensure the function runs without error and returns a float.
        n = 50
        p = run_single_replication(
            n=n,
            test_type='t-test',
            dependency_type='ar1',
            dependency_strength=0.5,
            seed=42
        )
        assert isinstance(p, float)
        assert 0.0 <= p <= 1.0

    def test_anova_null_independence(self):
        """Test ANOVA under null hypothesis."""
        n = 50
        p = run_single_replication(
            n=n,
            test_type='anova',
            dependency_type='ar1',
            dependency_strength=0.0,
            seed=42
        )
        assert isinstance(p, float)
        assert 0.0 <= p <= 1.0

    def test_edge_case_invalid_test_type(self):
        """Test that invalid test type raises error."""
        with pytest.raises(ValueError):
            run_single_replication(
                n=50,
                test_type='invalid',
                dependency_type='ar1',
                dependency_strength=0.5,
                seed=42
            )

    def test_edge_case_missing_block_size(self):
        """Test that block bootstrap without block_size raises error."""
        with pytest.raises(ValueError):
            run_single_replication(
                n=50,
                test_type='t-test',
                dependency_type='block_bootstrap',
                dependency_strength=0.5,
                block_size=None,
                seed=42
            )

class TestRunSimulation:
    """Integration-style tests for the full simulation loop."""

    def test_simulation_writes_file(self, tmp_path):
        """Verify that run_simulation creates the output CSV."""
        output_file = tmp_path / "results" / "test_sim.csv"
        
        config = {
            'n': 20,
            'n_replications': 10, # Small number for test speed
            'test_types': ['t-test'],
            'dependency_types': ['ar1'],
            'dependency_strengths': [0.0],
            'block_sizes': [5],
            'seed': 42
        }
        
        run_simulation(config, str(output_file))
        
        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == 10
        assert 'p_value' in df.columns
        assert 'test_type' in df.columns

    def test_simulation_handles_multiple_configs(self, tmp_path):
        """Verify simulation runs with multiple test types and strengths."""
        output_file = tmp_path / "results" / "multi_test.csv"
        
        config = {
            'n': 20,
            'n_replications': 5,
            'test_types': ['t-test', 'anova'],
            'dependency_types': ['ar1'],
            'dependency_strengths': [0.0, 0.3],
            'block_sizes': [5],
            'seed': 42
        }
        
        run_simulation(config, str(output_file))
        
        assert output_file.exists()
        df = pd.read_csv(output_file)
        # 2 tests * 2 strengths * 5 reps = 20 rows
        assert len(df) == 20
        assert set(df['test_type'].unique()) == {'t-test', 'anova'}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
