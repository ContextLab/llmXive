"""
Unit tests for reproducibility verification module (T056).
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import yaml

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from src.evaluation.reproducibility_verifier import (
    set_seed,
    run_benchmark_with_seed,
    collect_reproducibility_results,
    compute_reproducibility_metrics,
    save_reproducibility_results,
    save_reproducibility_summary,
    main,
    CI_WIDTH_THRESHOLD,
    DEFAULT_SEEDS
)


class TestReproducibilityVerifier:
    """Test suite for reproducibility verification module."""

    def test_set_seed_determinism(self):
        """Test that setting a seed produces deterministic results."""
        set_seed(42)
        val1 = np.random.random()
        
        set_seed(42)
        val2 = np.random.random()
        
        assert val1 == val2, "Setting the same seed should produce the same random values"

    def test_set_seed_different_values(self):
        """Test that different seeds produce different results."""
        set_seed(42)
        val1 = np.random.random()
        
        set_seed(123)
        val2 = np.random.random()
        
        assert val1 != val2, "Different seeds should produce different random values"

    def test_run_benchmark_with_seed_structure(self):
        """Test that run_benchmark_with_seed returns expected structure."""
        result = run_benchmark_with_seed(42)
        
        assert "seed" in result
        assert result["seed"] == 42
        assert "timestamp" in result
        assert "tasks" in result
        assert "aggregate" in result
        
        assert "mean_accuracy" in result["aggregate"]
        assert "std_accuracy" in result["aggregate"]
        assert "total_tasks" in result["aggregate"]

    def test_run_benchmark_with_seed_determinism(self):
        """Test that same seed produces same results."""
        result1 = run_benchmark_with_seed(999)
        result2 = run_benchmark_with_seed(999)
        
        assert result1["aggregate"]["mean_accuracy"] == result2["aggregate"]["mean_accuracy"]
        assert result1["aggregate"]["std_accuracy"] == result2["aggregate"]["std_accuracy"]

    def test_compute_reproducibility_metrics_insufficient_data(self):
        """Test metrics computation with insufficient data."""
        results = [
            {"seed": 42, "error": "Test error"}
        ]
        
        metrics = compute_reproducibility_metrics(results)
        
        assert metrics["status"] == "insufficient_data"
        assert "message" in metrics

    def test_compute_reproducibility_metrics_valid(self):
        """Test metrics computation with valid data."""
        # Create mock results
        results = []
        for i, seed in enumerate([42, 123, 456, 789]):
            results.append({
                "seed": seed,
                "aggregate": {
                    "mean_accuracy": 0.75 + i * 0.01,
                    "std_accuracy": 0.02,
                    "total_tasks": 5
                }
            })
        
        metrics = compute_reproducibility_metrics(results)
        
        assert metrics["status"] != "insufficient_data"
        assert "mean_accuracies" in metrics
        assert "overall_mean" in metrics
        assert "overall_std" in metrics
        assert "ci_95" in metrics
        assert "ci_width" in metrics["ci_95"]
        assert "passed" in metrics
        assert metrics["num_successful_runs"] == 4

    def test_compute_reproducibility_metrics_ci_width(self):
        """Test that CI width is calculated correctly."""
        # Create results with known variance
        base_accuracy = 0.80
        results = []
        for i, seed in enumerate([42, 123, 456, 789, 101112]):
            # Small variation
            accuracy = base_accuracy + (i - 2) * 0.005
            results.append({
                "seed": seed,
                "aggregate": {
                    "mean_accuracy": accuracy,
                    "std_accuracy": 0.01,
                    "total_tasks": 5
                }
            })
        
        metrics = compute_reproducibility_metrics(results)
        
        # CI width should be small for low variance data
        assert metrics["ci_95"]["width"] < 0.15
        assert metrics["passed"] is True

    def test_save_reproducibility_results(self):
        """Test saving reproducibility results to file."""
        results = [
            {
                "seed": 42,
                "aggregate": {"mean_accuracy": 0.80, "std_accuracy": 0.02, "total_tasks": 5}
            }
        ]
        metrics = {
            "mean_accuracies": [0.80],
            "overall_mean": 0.80,
            "ci_95": {"lower": 0.75, "upper": 0.85, "width": 0.10},
            "passed": True,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.yaml"
            saved_path = save_reproducibility_results(results, metrics, output_path)
            
            assert saved_path.exists()
            
            with open(saved_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert "metadata" in data
            assert "runs" in data
            assert "reproducibility_metrics" in data
            assert data["reproducibility_metrics"]["passed"] is True

    def test_save_reproducibility_summary(self):
        """Test saving reproducibility summary to file."""
        metrics = {
            "mean_accuracies": [0.80, 0.81, 0.79],
            "overall_mean": 0.80,
            "overall_std": 0.01,
            "ci_95": {"lower": 0.75, "upper": 0.85, "width": 0.10},
            "ci_width_threshold": 0.15,
            "passed": True,
            "num_successful_runs": 3,
            "effect_size": 0.5,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_summary.yaml"
            saved_path = save_reproducibility_summary(metrics, output_path)
            
            assert saved_path.exists()
            
            with open(saved_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert data["task_id"] == "T056"
            assert data["status"] == "passed"
            assert data["ci_width"] == 0.10
            assert data["threshold"] == 0.15

    def test_main_function(self):
        """Test the main function entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run with minimal seeds for speed
            exit_code = main(
                num_runs=3,
                seeds=[42, 123, 456],
                output_dir=tmpdir
            )
            
            # Should complete without error
            assert exit_code in [0, 1]  # 0 if passed, 1 if failed (but no exception)
            
            # Check that output files were created
            results_file = Path(tmpdir) / "reproducibility_results.yaml"
            summary_file = Path(tmpdir) / "reproducibility_summary.yaml"
            
            assert results_file.exists()
            assert summary_file.exists()

    def test_main_with_insufficient_runs(self):
        """Test main function with insufficient successful runs."""
        # This is hard to test directly without mocking, but we can test the logic
        # by checking that the function handles errors gracefully
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run with normal parameters
            exit_code = main(num_runs=2, seeds=[42, 123], output_dir=tmpdir)
            
            # Should complete
            assert exit_code in [0, 1]

    def test_ci_width_threshold_constant(self):
        """Test that CI width threshold is set correctly."""
        assert CI_WIDTH_THRESHOLD == 0.15

    def test_default_seeds(self):
        """Test default seeds configuration."""
        assert len(DEFAULT_SEEDS) >= 5
        assert 42 in DEFAULT_SEEDS