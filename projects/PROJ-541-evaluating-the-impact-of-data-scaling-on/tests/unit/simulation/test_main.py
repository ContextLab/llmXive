"""Unit tests for main.py simulation loop orchestration."""
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import pandas as pd
import csv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import (
    ensure_directories,
    run_single_iteration,
    save_partial_checkpoint,
    run_simulation_loop,
    save_results_to_csv
)
from simulation.config import SimulationConfig, get_default_config

class TestMain:
    """Test cases for main.py functions."""

    def test_ensure_directories_creates_folders(self, tmp_path):
        """Test that ensure_directories creates required directories."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            ensure_directories()
            assert mock_mkdir.called

    def test_run_single_iteration_returns_valid_result(self):
        """Test that run_single_iteration returns a valid result dictionary."""
        config = get_default_config()
        result = run_single_iteration(
            iteration_id=0,
            config=config,
            scaling_method="standardization",
            test_type="t_test",
            seed=42
        )
        
        assert result is not None
        assert "iteration_id" in result
        assert "config_id" in result
        assert "scaling_method" in result
        assert "test_type" in result
        assert "p_value" in result
        assert "statistic" in result
        assert "ground_truth" in result
        assert "scaling_params" in result
        assert "seed" in result

    def test_save_partial_checkpoint_writes_csv(self, tmp_path):
        """Test that save_partial_checkpoint writes a valid CSV file."""
        results = [
            {"iteration_id": 0, "value": 1.0},
            {"iteration_id": 1, "value": 2.0}
        ]
        checkpoint_path = str(tmp_path / "checkpoint.csv")
        
        save_partial_checkpoint(results, checkpoint_path)
        
        assert os.path.exists(checkpoint_path)
        
        with open(checkpoint_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert rows[0]["iteration_id"] == "0"
        assert rows[0]["value"] == "1.0"

    def test_save_results_to_csv_writes_file(self, tmp_path):
        """Test that save_results_to_csv writes a valid CSV file."""
        results = [
            {"iteration_id": 0, "p_value": 0.05, "statistic": 1.5},
            {"iteration_id": 1, "p_value": 0.03, "statistic": 2.1}
        ]
        output_path = str(tmp_path / "results.csv")
        
        save_results_to_csv(results, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert float(rows[0]["p_value"]) == 0.05

    @patch('main.run_single_iteration')
    @patch('main.save_partial_checkpoint')
    def test_run_simulation_loop_runs_iterations(self, mock_checkpoint, mock_run_iter, tmp_path):
        """Test that run_simulation_loop runs the correct number of iterations."""
        # Mock the run_single_iteration to return a valid result
        mock_run_iter.return_value = {
            "iteration_id": 0,
            "config_id": "test",
            "scaling_method": "standardization",
            "test_type": "t_test",
            "p_value": 0.05,
            "statistic": 1.5,
            "ground_truth": "null",
            "scaling_params": "{}",
            "seed": 42
        }
        
        config = get_default_config()
        output_path = str(tmp_path / "results.csv")
        checkpoint_path = str(tmp_path / "checkpoint.csv")
        
        # Run with small number of iterations for testing
        results = run_simulation_loop(
            config=config,
            iterations=5,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            checkpoint_interval=2
        )
        
        # Should run 5 iterations (1 config * 5 iterations)
        assert len(results) == 5
        assert mock_run_iter.call_count == 5

    def test_run_simulation_loop_saves_checkpoint(self, tmp_path):
        """Test that run_simulation_loop saves checkpoints at intervals."""
        config = get_default_config()
        output_path = str(tmp_path / "results.csv")
        checkpoint_path = str(tmp_path / "checkpoint.csv")
        
        # Run with checkpoint interval of 2
        results = run_simulation_loop(
            config=config,
            iterations=4,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            checkpoint_interval=2
        )
        
        # Checkpoint should be saved at least once
        assert os.path.exists(checkpoint_path)
        
        # Verify checkpoint file has content
        with open(checkpoint_path, 'r') as f:
            content = f.read()
            assert len(content) > 0