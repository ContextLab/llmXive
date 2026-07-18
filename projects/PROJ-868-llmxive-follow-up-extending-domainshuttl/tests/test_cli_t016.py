"""
Tests for the Dimensionality Sweep Script (T016).

Verifies that the orchestration logic correctly iterates through dimensions
and handles the output aggregation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cli import run_dimensionality_sweep
from src.config.settings import get_config


@pytest.fixture
def mock_training_metrics():
    """Fixture to return mock training metrics."""
    return {
        "final_loss": 0.05,
        "best_loss": 0.04,
        "epochs_run": 10,
        "converged": True,
        "device": "cpu",
    }


@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a temporary config with valid paths."""
    config = {
        "paths": {
            "processed_data": str(tmp_path),
            "raw_data": str(tmp_path / "raw"),
            "results": str(tmp_path / "results"),
        },
        "seeds": {"global_seed": 42},
        "hyperparameters": {
            "batch_size": 1,
            "learning_rate": 1e-4,
            "num_epochs": 2, # Fast test
            "early_stopping_patience": 10,
        },
        "fidelity_threshold": 0.85,
    }
    return config


def test_sweep_orchestration(mock_training_metrics):
    """
    Test that the sweep script iterates through all dimensions and aggregates logs.
    """
    dimensions = [16, 32] # Reduced for test speed
    
    with patch("src.cli.get_config") as mock_get_config, \
         patch("src.cli.train_autoencoder_for_dimension", return_value=mock_training_metrics):
        
        # Setup mock config
        mock_config = {
            "paths": {
                "processed_data": tempfile.gettempdir(),
            }
        }
        mock_get_config.return_value = mock_config

        # Run the sweep
        result = run_dimensionality_sweep()

        # Assertions
        assert "results" in result
        assert len(result["results"]) == len(dimensions)
        
        # Check that each dimension was processed
        processed_dims = [r["target_dimension"] for r in result["results"]]
        assert all(d in processed_dims for d in dimensions)

        # Check status
        for r in result["results"]:
            assert r["status"] == "completed"
            assert "metrics" in r
            assert r["metrics"]["final_loss"] == mock_training_metrics["final_loss"]

        # Check summary
        assert result["summary"]["successful"] == len(dimensions)
        assert result["summary"]["failed"] == 0

def test_sweep_handles_failures(mock_training_metrics):
    """
    Test that the sweep script handles failures gracefully and logs them.
    """
    dimensions = [16, 32]
    
    def side_effect(dim, *args, **kwargs):
        if dim == 32:
            raise RuntimeError("Simulated training failure")
        return mock_training_metrics

    with patch("src.cli.get_config") as mock_get_config, \
         patch("src.cli.train_autoencoder_for_dimension", side_effect=side_effect):
        
        mock_config = {
            "paths": {
                "processed_data": tempfile.gettempdir(),
            }
        }
        mock_get_config.return_value = mock_config

        result = run_dimensionality_sweep()

        # Check results
        assert len(result["results"]) == 2
        
        # Find the failed one
        failed_results = [r for r in result["results"] if r["target_dimension"] == 32]
        assert len(failed_results) == 1
        assert failed_results[0]["status"] == "failed"
        assert "error" in failed_results[0]
        assert "Simulated training failure" in failed_results[0]["error"]

        # Check summary
        assert result["summary"]["successful"] == 1
        assert result["summary"]["failed"] == 1
