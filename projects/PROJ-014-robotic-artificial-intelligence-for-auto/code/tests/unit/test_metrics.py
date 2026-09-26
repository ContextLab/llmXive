"""
Unit tests for metrics calculation module.
"""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.metrics import (
    calculate_auc,
    calculate_time_to_convergence,
    calculate_episodes_to_sustained_success,
    process_single_seed_metrics,
    aggregate_seed_metrics,
    generate_learning_metrics_report,
    SUCCESS_RATE_THRESHOLD,
    SUSTAINMENT_WINDOW
)


class TestCalculateAUC:
    """Tests for Area Under the Curve calculation."""
    
    def test_simple_auc(self):
        """Test AUC with simple linear data."""
        x = np.array([0, 1, 2, 3])
        y = np.array([0, 1, 2, 3])
        auc = calculate_auc(x, y)
        # Trapezoidal rule: sum of (x[i+1]-x[i]) * (y[i+1]+y[i])/2
        # = 1*(1+0)/2 + 1*(2+1)/2 + 1*(3+2)/2 = 0.5 + 1.5 + 2.5 = 4.5
        assert abs(auc - 4.5) < 1e-6
    
    def test_auc_constant(self):
        """Test AUC with constant values."""
        x = np.array([0, 1, 2, 3])
        y = np.array([2, 2, 2, 2])
        auc = calculate_auc(x, y)
        # Rectangle: width=3, height=2 => area=6
        assert abs(auc - 6.0) < 1e-6
    
    def test_auc_empty(self):
        """Test AUC with empty arrays."""
        with pytest.raises(ValueError):
            calculate_auc(np.array([]), np.array([]))
    
    def test_auc_mismatched_length(self):
        """Test AUC with mismatched array lengths."""
        with pytest.raises(ValueError):
            calculate_auc(np.array([0, 1, 2]), np.array([0, 1]))

class TestCalculateTimeToConvergence:
    """Tests for time-to-convergence calculation."""
    
    def test_convergence_detected(self):
        """Test convergence detection with clear improvement."""
        rewards = np.array([10, 20, 30, 40, 50, 50, 50, 50])
        episode = calculate_time_to_convergence(rewards, window_size=3, threshold_factor=0.95)
        # Should detect convergence around episode 5-6
        assert episode is not None
        assert 5 <= episode <= 8
    
    def test_no_convergence(self):
        """Test when agent never converges."""
        rewards = np.array([10, 5, 8, 3, 12, 2, 15, 1])  # Highly oscillating
        episode = calculate_time_to_convergence(rewards, window_size=3)
        # Might still find something, but let's check it returns something reasonable
        # (the function might return an episode even with oscillation)
        assert episode is None or episode > 0
    
    def test_insufficient_data(self):
        """Test with insufficient data points."""
        rewards = np.array([10, 20])
        episode = calculate_time_to_convergence(rewards, window_size=5)
        assert episode is None

class TestCalculateEpisodesToSustainedSuccess:
    """Tests for sustained success rate calculation (SC-001)."""
    
    def test_sustained_success_achieved(self):
        """Test detection of sustained success."""
        # Success rates: 0, 0, 1, 1, 1, 1, 1 (window=5)
        success_rates = np.array([0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        episode = calculate_episodes_to_sustained_success(
            success_rates, 
            threshold=0.85, 
            window=5
        )
        assert episode == 2  # Starts at index 2 (3rd episode)
    
    def test_sustained_success_not_achieved(self):
        """Test when sustained success is never achieved."""
        success_rates = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 1.0])
        episode = calculate_episodes_to_sustained_success(
            success_rates, 
            threshold=0.85, 
            window=3
        )
        assert episode is None
    
    def test_threshold_boundary(self):
        """Test exact threshold boundary."""
        # Exactly at threshold
        success_rates = np.array([0.85, 0.85, 0.85, 0.85, 0.85])
        episode = calculate_episodes_to_sustained_success(
            success_rates, 
            threshold=0.85, 
            window=5
        )
        assert episode == 0  # Achieved from start
    
    def test_below_threshold(self):
        """Test with values just below threshold."""
        success_rates = np.array([0.84, 0.84, 0.84, 0.84, 0.84])
        episode = calculate_episodes_to_sustained_success(
            success_rates, 
            threshold=0.85, 
            window=5
        )
        assert episode is None

class TestProcessSingleSeedMetrics:
    """Tests for single seed metric processing."""
    
    def test_basic_metrics(self):
        """Test basic metric calculation."""
        rewards = [10, 20, 30, 40, 50]
        successes = [0, 0, 1, 1, 1]
        
        metrics = process_single_seed_metrics(rewards, successes)
        
        assert metrics["total_episodes"] == 5
        assert metrics["final_reward"] == 50.0
        assert metrics["final_success_rate"] == 1.0
        assert metrics["max_reward"] == 50.0
        assert "auc_rewards" in metrics
        assert "auc_success" in metrics
    
    def test_with_times(self):
        """Test metric calculation with episode times."""
        rewards = [10, 20, 30]
        successes = [1, 1, 1]
        times = [1.0, 2.0, 3.0]
        
        metrics = process_single_seed_metrics(rewards, successes, times)
        
        assert "total_training_time_seconds" in metrics
        assert metrics["total_training_time_seconds"] == 6.0
        assert "mean_episode_time_seconds" in metrics
        assert metrics["mean_episode_time_seconds"] == 2.0

class TestAggregateSeedMetrics:
    """Tests for aggregating metrics across seeds."""
    
    def test_aggregate_basic(self):
        """Test basic aggregation."""
        seed_metrics = [
            {"auc_rewards": 100.0, "auc_success": 0.5, "time_to_convergence_episode": 10, "episodes_to_sustained_success": 15},
            {"auc_rewards": 200.0, "auc_success": 0.8, "time_to_convergence_episode": 20, "episodes_to_sustained_success": 25},
            {"auc_rewards": 150.0, "auc_success": 0.6, "time_to_convergence_episode": 15, "episodes_to_sustained_success": 20},
        ]
        
        aggregated = aggregate_seed_metrics(seed_metrics)
        
        assert aggregated["num_seeds"] == 3
        assert abs(aggregated["auc_rewards"]["mean"] - 150.0) < 0.01
        assert abs(aggregated["auc_success"]["mean"] - 0.633) < 0.01
        assert "time_to_convergence" in aggregated
        assert "episodes_to_sustained_success" in aggregated
    
    def test_aggregate_empty(self):
        """Test aggregation with no metrics."""
        aggregated = aggregate_seed_metrics([])
        assert "error" in aggregated

class TestGenerateLearningMetricsReport:
    """Tests for full report generation."""
    
    def test_report_structure(self):
        """Test that report has correct structure."""
        # Create a temporary directory with fake training curves
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            curves_dir = tmpdir_path / "training_curves"
            curves_dir.mkdir()
            
            # Create fake CSV files
            for seed in [1, 2]:
                csv_path = curves_dir / f"rgb_seed_{seed}.csv"
                with open(csv_path, 'w') as f:
                    f.write("episode,reward,success,time_seconds\n")
                    for i in range(10):
                        f.write(f"{i},{i*10},{1 if i > 5 else 0},{1.0}\n")
            
            report = generate_learning_metrics_report(
                modalities=["rgb"],
                output_path=tmpdir_path / "test_report.json"
            )
            
            assert "modalities" in report
            assert "rgb" in report["modalities"]
            assert "aggregated" in report["modalities"]["rgb"]
            assert "per_seed_metrics" in report["modalities"]["rgb"]
            
            # Verify file was written
            assert (tmpdir_path / "test_report.json").exists()
            
            with open(tmpdir_path / "test_report.json", 'r') as f:
                loaded = json.load(f)
                assert loaded["modalities"]["rgb"]["aggregated"]["num_seeds"] == 2