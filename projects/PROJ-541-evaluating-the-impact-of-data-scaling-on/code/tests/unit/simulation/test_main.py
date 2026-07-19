"""
Unit tests for code/main.py, specifically focusing on the iteration threshold enforcement.
"""
import pytest
import sys
import os
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import enforce_iteration_threshold, ensure_directories, RESULTS_FILE, CHECKPOINT_FILE

class TestMain:
    """Tests for main.py utilities."""

    def test_enforce_iteration_threshold_meets_minimum(self):
        """Test that iterations >= 10000 are returned as-is."""
        result = enforce_iteration_threshold(10000)
        assert result == 10000

        result = enforce_iteration_threshold(50000)
        assert result == 50000

    def test_enforce_iteration_threshold_below_minimum(self):
        """Test that iterations < 10000 are bumped to 10000."""
        result = enforce_iteration_threshold(100)
        assert result == 10000

        result = enforce_iteration_threshold(9999)
        assert result == 10000

    def test_enforce_iteration_threshold_custom_minimum(self):
        """Test enforcement with a custom minimum."""
        result = enforce_iteration_threshold(500, minimum=1000)
        assert result == 1000

        result = enforce_iteration_threshold(2000, minimum=1000)
        assert result == 2000

    def test_iteration_threshold_assertion(self):
        """
        Verification test asserting iterations >= 10000.
        This directly validates the requirement from T063a.
        """
        # Simulate a request for too few iterations
        requested = 100
        final = enforce_iteration_threshold(requested, minimum=10000)
        
        # Assert the enforcement worked
        assert final >= 10000, f"Enforced iterations {final} should be >= 10000"
        assert final == 10000, f"Enforced iterations should be exactly 10000 when requested 100"

        # Simulate a request for enough iterations
        requested = 20000
        final = enforce_iteration_threshold(requested, minimum=10000)
        assert final >= 10000
        assert final == 20000

    def test_enforce_iteration_threshold_zero(self):
        """Test that zero iterations are bumped to minimum."""
        result = enforce_iteration_threshold(0)
        assert result == 10000

    def test_enforce_iteration_threshold_negative(self):
        """Test that negative iterations are bumped to minimum."""
        result = enforce_iteration_threshold(-500)
        assert result == 10000

    def test_ensure_directories(self):
        """Test that ensure_directories creates required directories."""
        ensure_directories()
        
        # Check that key directories exist
        assert os.path.exists("data/raw")
        assert os.path.exists("data/scaled")
        assert os.path.exists("results/figures")
        assert os.path.exists("logs")

    def test_simulation_results_schema(self):
        """
        Test that the simulation results file has the correct schema.
        This validates the deliverable from T028.
        """
        # Run a small simulation to generate results
        from simulation.config import SimulationConfig
        from main import run_simulation_loop
        from simulation.logger import get_logger

        config = SimulationConfig(
            config_id="test-schema",
            distribution_types=["normal"],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            n_samples=100,
            effect_size=0.5,
            alpha=0.05,
            seed_base=42,
            null_hypothesis_mean_diff=0.0,
            alternative_hypothesis_mean_diff=1.0
        )

        logger = get_logger("test_schema")
        results_df = run_simulation_loop(config, 100, logger)

        # Verify schema
        expected_columns = [
            "iteration_id", "config_id", "scaling_method", "test_type",
            "p_value", "statistic", "ground_truth", "scaling_params", "seed"
        ]

        assert list(results_df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, got {list(results_df.columns)}"

        # Verify row count
        assert len(results_df) == 100, f"Expected 100 rows, got {len(results_df)}"

        # Verify data types
        assert results_df['iteration_id'].dtype in ['int64', 'int32']
        assert results_df['seed'].dtype in ['int64', 'int32']
        assert results_df['p_value'].dtype in ['float64', 'float32']

    def test_checkpoint_mechanism(self):
        """
        Test that checkpoint mechanism works correctly.
        """
        from simulation.config import SimulationConfig
        from main import run_simulation_loop, CHECKPOINT_FILE
        from simulation.logger import get_logger
        import os

        config = SimulationConfig(
            config_id="test-checkpoint",
            distribution_types=["normal"],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            n_samples=100,
            effect_size=0.5,
            alpha=0.05,
            seed_base=42,
            null_hypothesis_mean_diff=0.0,
            alternative_hypothesis_mean_diff=1.0
        )

        logger = get_logger("test_checkpoint")
        
        # Run with more iterations than checkpoint interval
        results_df = run_simulation_loop(config, 2500, logger)

        # Check that checkpoint file exists
        assert os.path.exists(CHECKPOINT_FILE), "Checkpoint file should exist"

        # Load checkpoint and verify it has data
        checkpoint_df = pd.read_csv(CHECKPOINT_FILE)
        assert len(checkpoint_df) > 0, "Checkpoint file should contain data"

        # Clean up
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)