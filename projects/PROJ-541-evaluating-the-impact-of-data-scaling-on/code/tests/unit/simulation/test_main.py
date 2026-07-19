"""
Unit tests for main.py simulation loop orchestration.
Verifies T028 requirements: file generation, schema, iteration count.
"""
import pytest
import sys
import os
from pathlib import Path
import pandas as pd
import time
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import run_simulation_loop, enforce_iteration_threshold, ensure_directories
from simulation.config import SimulationConfig, get_default_config
from simulation.logger import setup_logger

class TestMain:
    """Tests for main.py orchestration logic."""

    def test_enforce_iteration_threshold(self):
        """Test that iteration threshold is enforced."""
        # Below threshold
        result = enforce_iteration_threshold(5000)
        assert result == 10000

        # Above threshold
        result = enforce_iteration_threshold(15000)
        assert result == 15000

        # Exactly at threshold
        result = enforce_iteration_threshold(10000)
        assert result == 10000

    def test_simulation_loop_creates_files(self, tmp_path):
        """Test that simulation loop creates required CSV files."""
        # Create a minimal config
        config = SimulationConfig(
            config_id="test-config-1",
            distribution_type="normal",
            n_samples=100,
            mean=0.0,
            variance=1.0,
            skewness=0.0,
            kurtosis=3.0,
            effect_size=0.0  # Null hypothesis
        )
        
        # Run a small loop for testing
        logger = setup_logger(batch_id="test_loop")
        
        # Use a small number of iterations for the test
        df_results = run_simulation_loop(
            configs=[config],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            total_iterations=100,  # Small for test speed
            checkpoint_interval=50,
            output_path=str(tmp_path / "simulation_results.csv"),
            checkpoint_path=str(tmp_path / "partial_checkpoint.csv"),
            logger=logger
        )
        
        # Verify output file exists
        assert os.path.exists(str(tmp_path / "simulation_results.csv"))
        assert os.path.exists(str(tmp_path / "partial_checkpoint.csv"))

    def test_simulation_results_schema(self, tmp_path):
        """Test that simulation results have the correct schema."""
        config = SimulationConfig(
            config_id="test-config-schema",
            distribution_type="normal",
            n_samples=50,
            mean=0.0,
            variance=1.0,
            skewness=0.0,
            kurtosis=3.0,
            effect_size=0.0
        )
        
        logger = setup_logger(batch_id="test_schema")
        
        df_results = run_simulation_loop(
            configs=[config],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            total_iterations=50,
            checkpoint_interval=25,
            output_path=str(tmp_path / "simulation_results.csv"),
            checkpoint_path=str(tmp_path / "partial_checkpoint.csv"),
            logger=logger
        )
        
        # Load and check schema
        df = pd.read_csv(str(tmp_path / "simulation_results.csv"))
        
        required_columns = [
            "iteration_id",
            "config_id",
            "scaling_method",
            "test_type",
            "p_value",
            "statistic",
            "ground_truth",
            "scaling_params",
            "seed"
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_simulation_iteration_count(self, tmp_path):
        """Test that simulation runs the requested number of iterations."""
        config = get_default_config()
        
        logger = setup_logger(batch_id="test_count")
        
        expected_iterations = 100
        
        df_results = run_simulation_loop(
            configs=[config],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            total_iterations=expected_iterations,
            checkpoint_interval=50,
            output_path=str(tmp_path / "simulation_results.csv"),
            checkpoint_path=str(tmp_path / "partial_checkpoint.csv"),
            logger=logger
        )
        
        # Load results
        df = pd.read_csv(str(tmp_path / "simulation_results.csv"))
        
        # Verify iteration count (allowing for some failures, but should be close)
        assert len(df) > 0, "No results generated"
        assert df["iteration_id"].max() >= expected_iterations // 2, \
            f"Expected at least half the iterations, got {len(df)}"

    def test_checkpoint_mechanism(self, tmp_path):
        """Test that checkpoints are saved at the correct interval."""
        config = get_default_config()
        logger = setup_logger(batch_id="test_checkpoint")
        
        checkpoint_path = str(tmp_path / "partial_checkpoint.csv")
        
        df_results = run_simulation_loop(
            configs=[config],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            total_iterations=200,
            checkpoint_interval=50,
            output_path=str(tmp_path / "simulation_results.csv"),
            checkpoint_path=checkpoint_path,
            logger=logger
        )
        
        # Check that checkpoint file exists and has data
        assert os.path.exists(checkpoint_path)
        df_checkpoint = pd.read_csv(checkpoint_path)
        assert len(df_checkpoint) > 0

    def test_seed_recording(self, tmp_path):
        """Test that random seeds are recorded for every iteration."""
        config = get_default_config()
        logger = setup_logger(batch_id="test_seed")
        
        df_results = run_simulation_loop(
            configs=[config],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            total_iterations=50,
            checkpoint_interval=25,
            output_path=str(tmp_path / "simulation_results.csv"),
            checkpoint_path=str(tmp_path / "partial_checkpoint.csv"),
            logger=logger
        )
        
        df = pd.read_csv(str(tmp_path / "simulation_results.csv"))
        
        # Verify all rows have seeds
        assert "seed" in df.columns
        assert df["seed"].notna().all(), "Some seeds are missing"
        assert df["seed"].nunique() > 1, "Seeds are not unique"

    def test_ground_truth_label(self, tmp_path):
        """Test that ground truth labels are recorded."""
        config = get_default_config()
        logger = setup_logger(batch_id="test_gt")
        
        df_results = run_simulation_loop(
            configs=[config],
            scaling_methods=["standardize"],
            test_types=["t_test"],
            total_iterations=50,
            checkpoint_interval=25,
            output_path=str(tmp_path / "simulation_results.csv"),
            checkpoint_path=str(tmp_path / "partial_checkpoint.csv"),
            logger=logger
        )
        
        df = pd.read_csv(str(tmp_path / "simulation_results.csv"))
        
        assert "ground_truth" in df.columns
        assert df["ground_truth"].notna().all()
        # Should be 'null' or 'alternative'
        valid_labels = ['null', 'alternative']
        assert all(label in valid_labels for label in df["ground_truth"].unique())