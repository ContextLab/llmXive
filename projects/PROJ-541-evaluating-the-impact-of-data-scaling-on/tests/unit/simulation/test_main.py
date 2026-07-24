"""Unit tests for code/main.py functionality."""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from main import write_simulation_results, run_simulation_loop
from simulation.config import SimulationConfig


class TestMain:
    """Tests for main.py functions."""

    def test_write_simulation_results_creates_file(self, tmp_path):
        """Test that write_simulation_results creates the output CSV."""
        output_path = tmp_path / "test_results.csv"
        results = [
            {
                "iteration_id": 0,
                "config_id": "config_Normal_42",
                "scaling_method": "standardize",
                "test_type": "t_test",
                "p_value": 0.03,
                "statistic": 2.1,
                "ground_truth": "null",
                "scaling_params": "{}",
                "seed": 42,
            }
        ]
        
        write_simulation_results(results, str(output_path))
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["iteration_id"] == "0"
            assert rows[0]["p_value"] == "0.03"

    def test_write_simulation_results_schema(self, tmp_path):
        """Test that the output CSV contains the correct schema."""
        output_path = tmp_path / "schema_test.csv"
        results = [
            {
                "iteration_id": 1,
                "config_id": "config_Skewed_123",
                "scaling_method": "minmax",
                "test_type": "anova",
                "p_value": 0.001,
                "statistic": 5.4,
                "ground_truth": "alternative",
                "scaling_params": json.dumps({"min": 0, "max": 1}),
                "seed": 123,
            }
        ]
        
        write_simulation_results(results, str(output_path))
        
        df = pd.read_csv(output_path)
        expected_cols = [
            "iteration_id", "config_id", "scaling_method", "test_type",
            "p_value", "statistic", "ground_truth", "scaling_params", "seed"
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_write_simulation_results_empty(self, tmp_path):
        """Test that write_simulation_results handles empty results gracefully."""
        output_path = tmp_path / "empty_results.csv"
        
        write_simulation_results([], str(output_path))
        
        # File should exist but be empty or have only headers depending on implementation
        # For this test, we just ensure it doesn't crash
        assert output_path.exists()

    @patch("main.run_single_iteration")
    def test_run_simulation_loop_calls_iterations(self, mock_run_iter, tmp_path):
        """Test that run_simulation_loop calls run_single_iteration the correct number of times."""
        # Mock the iteration result
        mock_run_iter.return_value = {
            "iteration_id": 0,
            "config_id": "test_config",
            "scaling_method": "standardize",
            "test_type": "t_test",
            "p_value": 0.05,
            "statistic": 1.96,
            "ground_truth": "null",
            "scaling_params": "{}",
            "seed": 1,
        }
        
        # Create a minimal config
        config = SimulationConfig(
            distribution_type="Normal",
            mean=0.0,
            variance=1.0,
            skewness=0.0,
            kurtosis=3.0,
        )
        
        # Run with 2 iterations
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch CONFIG_MATRIX
            with patch("main.CONFIG_MATRIX", [config]):
                with patch("main.write_simulation_results") as mock_write:
                    result_df = run_simulation_loop(
                        target_iterations=2,
                        config_matrix=[config],
                        scaling_methods=["standardize"],
                        test_types=["t_test"],
                    )
                    
                    # Check that run_single_iteration was called 2 times (1 config * 2 iterations * 1 scale * 1 test)
                    assert mock_run_iter.call_count == 2
                    assert len(result_df) == 2

    def test_write_simulation_results_multiple_rows(self, tmp_path):
        """Test writing multiple rows to CSV."""
        output_path = tmp_path / "multi_row.csv"
        results = [
            {
                "iteration_id": i,
                "config_id": f"config_{i}",
                "scaling_method": "standardize",
                "test_type": "t_test",
                "p_value": 0.05 * (i + 1),
                "statistic": 1.96 + i,
                "ground_truth": "null",
                "scaling_params": "{}",
                "seed": i * 10,
            }
            for i in range(10)
        ]
        
        write_simulation_results(results, str(output_path))
        
        df = pd.read_csv(output_path)
        assert len(df) == 10
        assert df["iteration_id"].tolist() == list(range(10))
        assert df["seed"].tolist() == [i * 10 for i in range(10)]