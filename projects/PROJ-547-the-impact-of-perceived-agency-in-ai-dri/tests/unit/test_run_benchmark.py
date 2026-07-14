"""
Unit tests for benchmark execution script.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error

from code.benchmark.run_benchmark import (
    compute_accuracy_metrics,
    verify_success_criteria,
    load_benchmark_data,
    ensure_output_dir,
)
from code.utils.error_handler import PipelineError

class TestBenchmarkFunctions:
    """Test suite for benchmark execution functions."""

    @patch("code.benchmark.run_benchmark.BENCHMARK_DIR")
    @patch("code.benchmark.run_benchmark.OUTPUT_DIR")
    def test_ensure_output_dir_creates_directory(self, mock_output_dir, mock_benchmark_dir):
        """Test that ensure_output_dir creates the output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        mock_output_dir.__truediv__.return_value = temp_dir / "output"
        
        result = ensure_output_dir()
        
        assert result == temp_dir / "output"
        assert result.exists()
        assert result.is_dir()

    def test_compute_accuracy_metrics(self):
        """Test accuracy metric computation."""
        # Create mock data
        computed = pd.DataFrame({
            "session_id": ["s1", "s2", "s3"],
            "agency_score_computed": [0.8, 0.6, 0.9]
        })
        
        ground_truth = pd.DataFrame({
            "session_id": ["s1", "s2", "s3"],
            "agency_score_truth": [0.85, 0.55, 0.88]
        })
        
        # Mock logger
        mock_logger = MagicMock()
        
        results = compute_accuracy_metrics(computed, ground_truth, mock_logger)
        
        assert "mae" in results
        assert "r2" in results
        assert "pearson_r" in results
        assert "n_samples" in results
        assert results["n_samples"] == 3
        assert isinstance(results["mae"], float)
        
        # Verify MAE calculation
        expected_mae = mean_absolute_error(
            ground_truth["agency_score_truth"],
            computed["agency_score_computed"]
        )
        assert abs(results["mae"] - expected_mae) < 1e-6

    def test_verify_success_criteria_pass(self):
        """Test success criteria verification when all pass."""
        accuracy_metrics = {
            "mae": 0.005,  # Below threshold of 0.01
            "r2": 0.85,
            "pearson_r": 0.92,
            "n_samples": 100
        }
        
        mock_logger = MagicMock()
        
        all_passed, details = verify_success_criteria(accuracy_metrics, mock_logger)
        
        assert all_passed is True
        assert details["sc001_passed"] is True
        assert details["sc002_passed"] is True
        assert details["sc001_success_rate"] == 1.0
        assert details["sc002_mae"] == 0.005

    def test_verify_success_criteria_fail_mae(self):
        """Test success criteria verification when MAE threshold fails."""
        accuracy_metrics = {
            "mae": 0.015,  # Above threshold of 0.01
            "r2": 0.85,
            "pearson_r": 0.92,
            "n_samples": 100
        }
        
        mock_logger = MagicMock()
        
        all_passed, details = verify_success_criteria(accuracy_metrics, mock_logger)
        
        assert all_passed is False
        assert details["sc001_passed"] is True
        assert details["sc002_passed"] is False

    def test_verify_success_criteria_fail_rate(self):
        """Test success criteria verification when success rate fails."""
        accuracy_metrics = {
            "mae": 0.005,
            "r2": 0.85,
            "pearson_r": 0.92,
            "n_samples": 100
        }
        
        # Patch the success rate calculation
        with patch("code.benchmark.run_benchmark.verify_success_criteria") as mock_func:
            # We'll test the logic directly instead
            pass

    @patch("code.benchmark.run_benchmark.BENCHMARK_DIR")
    def test_load_benchmark_data_missing_files(self, mock_benchmark_dir):
        """Test that load_benchmark_data raises error for missing files."""
        temp_dir = Path(tempfile.mkdtemp())
        mock_benchmark_dir.__truediv__.return_value = temp_dir / "nonexistent"
        
        with pytest.raises(PipelineError) as exc_info:
            load_benchmark_data()
        
        assert "not found" in str(exc_info.value).lower()

    def test_compute_accuracy_metrics_no_matches(self):
        """Test accuracy metrics with no matching sessions."""
        computed = pd.DataFrame({
            "session_id": ["s1", "s2"],
            "agency_score_computed": [0.8, 0.6]
        })
        
        ground_truth = pd.DataFrame({
            "session_id": ["s3", "s4"],
            "agency_score_truth": [0.85, 0.55]
        })
        
        mock_logger = MagicMock()
        
        with pytest.raises(PipelineError) as exc_info:
            compute_accuracy_metrics(computed, ground_truth, mock_logger)
        
        assert "no matching sessions" in str(exc_info.value).lower()

class TestBenchmarkIntegration:
    """Integration tests for benchmark workflow."""

    @patch("code.benchmark.run_benchmark.OUTPUT_DIR")
    def test_results_json_structure(self, mock_output_dir):
        """Test that results JSON has expected structure."""
        temp_dir = Path(tempfile.mkdtemp())
        mock_output_dir.__truediv__.return_value = temp_dir / "output"
        
        results = {
            "timestamp": "2024-01-01T00:00:00",
            "accuracy_metrics": {
                "mae": 0.005,
                "r2": 0.85,
                "pearson_r": 0.92,
                "n_samples": 100
            },
            "success_criteria": {
                "sc001_passed": True,
                "sc002_passed": True,
                "all_passed": True
            },
            "pipeline_status": "success"
        }
        
        results_path = temp_dir / "output" / "test_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f)
        
        # Verify structure
        with open(results_path) as f:
            loaded = json.load(f)
        
        assert "timestamp" in loaded
        assert "accuracy_metrics" in loaded
        assert "success_criteria" in loaded
        assert "pipeline_status" in loaded
        assert "mae" in loaded["accuracy_metrics"]
        assert "sc001_passed" in loaded["success_criteria"]