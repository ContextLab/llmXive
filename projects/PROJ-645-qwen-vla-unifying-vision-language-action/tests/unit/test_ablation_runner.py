"""
Unit tests for the Ablation Runner (T025).
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.ablation_runner import (
    run_single_ablation_run,
    aggregate_results,
    save_csv,
    plot_results
)
from src.utils.config import Config

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create necessary subdirectories
        Path(tmpdir, "data").mkdir()
        Path(tmpdir, "figures").mkdir()
        # Create dummy seeds file
        seeds_path = Path(tmpdir, "seeds.json")
        with open(seeds_path, 'w') as f:
            json.dump([123, 456], f)
        yield tmpdir

@pytest.fixture
def mock_config():
    config = Config()
    config.data_ratio = 0.5
    config.seed = 123
    config.epochs = 1
    config.batch_size = 4
    return config

def test_run_single_ablation_run_success(mock_config, temp_dir, tmp_path):
    """Test that a single run completes and returns expected structure."""
    # Mock the heavy dependencies
    with patch('src.experiments.ablation_runner.train_loop') as mock_train, \
         patch('src.experiments.ablation_runner.run_libero_evaluation') as mock_eval, \
         patch('src.experiments.ablation_runner.Path') as mock_path, \
         patch('src.experiments.ablation_logger') as mock_logger:
        
        # Setup mocks
        mock_train.return_value = str(tmp_path / "checkpoint.pt")
        # Create dummy checkpoint
        (tmp_path / "checkpoint.pt").touch()
        
        mock_eval.return_value = {
            'success_rate': [0.8, 0.9, 0.85], # List of rates
            'trajectory_length': 100
        }
        
        # Mock Path to use temp_dir
        original_path = Path
        def mock_path_constructor(*args, **kwargs):
            if args and str(args[0]).startswith("data"):
                return original_path(temp_dir, *args[1:], **kwargs)
            return original_path(*args, **kwargs)
        
        mock_path.side_effect = mock_path_constructor

        # Mock logger
        mock_logger = MagicMock()

        result = run_single_ablation_run(0.5, 123, mock_config, mock_logger)

        assert result['ratio'] == 0.5
        assert result['seed'] == 123
        assert 'success_rate' in result
        assert result['success_rate'] == 0.85 # (0.8+0.9+0.85)/3
        assert result['error'] is None

def test_aggregate_results():
    """Test aggregation logic and CI calculation."""
    results = [
        {"ratio": 0.0, "seed": 1, "success_rate": 0.5},
        {"ratio": 0.0, "seed": 2, "success_rate": 0.6},
        {"ratio": 0.5, "seed": 1, "success_rate": 0.7},
        {"ratio": 0.5, "seed": 2, "success_rate": 0.8},
        {"ratio": 1.0, "seed": 1, "success_rate": 0.9},
        {"ratio": 1.0, "seed": 2, "success_rate": 0.95},
    ]

    aggregated = aggregate_results(results)

    assert "0.0" in aggregated
    assert "0.5" in aggregated
    assert "1.0" in aggregated

    # Check mean calculation (simple average for 2 items)
    assert abs(aggregated["0.0"]["mean_success_rate"] - 0.55) < 0.01
    assert abs(aggregated["0.5"]["mean_success_rate"] - 0.75) < 0.01
    assert abs(aggregated["1.0"]["mean_success_rate"] - 0.925) < 0.01

    # Check CI bounds are reasonable (lower < mean < upper)
    for r in aggregated:
        assert aggregated[r]["ci_lower"] <= aggregated[r]["mean_success_rate"]
        assert aggregated[r]["mean_success_rate"] <= aggregated[r]["ci_upper"]

def test_save_csv(tmp_path):
    """Test CSV generation."""
    aggregated = {
        "0.0": {"ratio": 0.0, "mean_success_rate": 0.5, "ci_lower": 0.4, "ci_upper": 0.6, "n_seeds": 2},
        "1.0": {"ratio": 1.0, "mean_success_rate": 0.9, "ci_lower": 0.8, "ci_upper": 1.0, "n_seeds": 2},
    }
    csv_path = tmp_path / "test_ablation.csv"
    save_csv(aggregated, str(csv_path))

    assert csv_path.exists()
    with open(csv_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 3 # Header + 2 data rows
        assert "ratio" in lines[0]

def test_plot_results(tmp_path):
    """Test plot generation."""
    aggregated = {
        "0.0": {"ratio": 0.0, "mean_success_rate": 0.5, "ci_lower": 0.4, "ci_upper": 0.6, "n_seeds": 2},
        "1.0": {"ratio": 1.0, "mean_success_rate": 0.9, "ci_lower": 0.8, "ci_upper": 1.0, "n_seeds": 2},
    }
    plot_path = tmp_path / "test_plot.png"
    plot_results(aggregated, str(plot_path))

    assert plot_path.exists()
    assert plot_path.stat().st_size > 0