import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.performance_timer import (
    estimate_training_time,
    run_performance_benchmark,
    CI_TIME_LIMIT_HOURS,
    CI_TIME_LIMIT_SECONDS
)

class TestPerformanceTimer:
    """Unit tests for performance timing and benchmarking."""

    def test_estimate_training_time_under_limit(self):
        """Test estimation for small dataset that should be under limit."""
        result = estimate_training_time(
            n_samples=100,
            n_features=5,
            n_trees=50,
            max_depth=4,
            n_folds=5
        )
        
        assert result["is_within_limit"] is True
        assert result["estimated_seconds"] > 0
        assert result["recommendation"] == "PASS"

    def test_estimate_training_time_over_limit(self):
        """Test estimation for massive dataset that should exceed limit."""
        result = estimate_training_time(
            n_samples=1000000,  # 1M samples
            n_features=50,
            n_trees=500,
            max_depth=15,
            n_folds=5
        )
        
        assert result["is_within_limit"] is False
        assert result["recommendation"] == "OPTIMIZE"

    def test_estimate_training_time_scaling(self):
        """Test that time scales with sample size."""
        result_100 = estimate_training_time(n_samples=100, n_features=5)
        result_200 = estimate_training_time(n_samples=200, n_features=5)
        
        # Should be roughly linear with samples
        assert result_200["estimated_seconds"] > result_100["estimated_seconds"]

    @patch('src.utils.performance_timer.enforce_cpu_mode')
    @patch('src.utils.performance_timer.register_artifact')
    def test_run_performance_benchmark_success(
        self, 
        mock_register, 
        mock_enforce_cpu
    ):
        """Test successful benchmark execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create mock data
            data = pd.DataFrame({
                'mean_coordination_number': np.random.rand(100),
                'electronegativity_variance': np.random.rand(100),
                'atomic_radius_variance': np.random.rand(100),
                'Tg': np.random.rand(100) * 500 + 300
            })
            
            data_path = tmp_path / "preprocessed_data.csv"
            data.to_csv(data_path, index=False)
            
            output_path = tmp_path / "test_benchmark.json"
            
            # Run benchmark
            results = run_performance_benchmark(
                data_path=data_path,
                output_path=output_path,
                n_trees=10,  # Small for test speed
                max_depth=3
            )
            
            assert results["status"] == "PASS" or results["status"] == "FAIL"
            assert "actual_seconds" in results
            assert "is_within_limit" in results
            assert results["n_samples"] == 100
            
            # Check file was written
            assert output_path.exists()
            
            with open(output_path) as f:
                saved = json.load(f)
            assert saved["status"] == results["status"]

    def test_benchmark_handles_missing_data(self):
        """Test that benchmark fails gracefully with missing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "missing_data_benchmark.json"
            missing_path = tmp_path / "nonexistent.csv"
            
            with pytest.raises(FileNotFoundError):
                run_performance_benchmark(missing_path, output_path)

    def test_benchmark_handles_nan_values(self):
        """Test that benchmark handles NaN values in data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create data with NaN
            data = pd.DataFrame({
                'mean_coordination_number': [1.0, 2.0, np.nan, 4.0],
                'electronegativity_variance': [0.1, 0.2, 0.3, np.nan],
                'atomic_radius_variance': [0.5, 0.6, 0.7, 0.8],
                'Tg': [300.0, 350.0, 400.0, 450.0]
            })
            
            data_path = tmp_path / "nan_data.csv"
            data.to_csv(data_path, index=False)
            
            output_path = tmp_path / "nan_benchmark.json"
            
            # Should not crash, should filter NaNs
            results = run_performance_benchmark(
                data_path=data_path,
                output_path=output_path,
                n_trees=5,
                max_depth=2
            )
            
            # Should have fewer samples than original due to NaN filtering
            assert results["n_samples"] < 4
            assert results["status"] in ["PASS", "FAIL"]

    def test_cpu_mode_enforced(self):
        """Verify CPU mode is enforced during benchmark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            data = pd.DataFrame({
                'mean_coordination_number': np.random.rand(50),
                'electronegativity_variance': np.random.rand(50),
                'atomic_radius_variance': np.random.rand(50),
                'Tg': np.random.rand(50) * 500 + 300
            })
            
            data_path = tmp_path / "cpu_test.csv"
            data.to_csv(data_path, index=False)
            output_path = tmp_path / "cpu_test.json"
            
            with patch('src.utils.performance_timer.enforce_cpu_mode') as mock_cpu:
                run_performance_benchmark(data_path, output_path, n_trees=5)
                mock_cpu.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])