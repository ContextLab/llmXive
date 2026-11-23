import pytest
import numpy as np
from sklearn.utils.stats import var as sklearn_var
from main import compute_variance_metrics, TEMPERATURES, SEEDS_PER_TEMP

class TestTemperatureSweep:
    """Unit tests for temperature sweep variance computation."""

    def test_compute_variance_metrics_single_temperature(self):
        """Test variance computation for a single temperature."""
        results = [
            {"seed": 0, "temperature": 0.5, "final_accuracy": 0.85, "status": "completed"},
            {"seed": 1, "temperature": 0.5, "final_accuracy": 0.87, "status": "completed"},
            {"seed": 2, "temperature": 0.5, "final_accuracy": 0.86, "status": "completed"},
        ]
        
        report = compute_variance_metrics(results)
        
        assert "variance_by_temperature" in report
        assert "0.5" in report["variance_by_temperature"]
        
        metrics = report["variance_by_temperature"]["0.5"]
        assert metrics["count"] == 3
        assert abs(metrics["mean"] - 0.86) < 0.01
        
        # Verify variance calculation matches sklearn
        expected_var = float(sklearn_var([0.85, 0.87, 0.86]))
        assert abs(metrics["variance"] - expected_var) < 1e-6

    def test_compute_variance_metrics_multiple_temperatures(self):
        """Test variance computation across multiple temperatures."""
        results = [
            {"seed": 0, "temperature": 0.5, "final_accuracy": 0.85, "status": "completed"},
            {"seed": 1, "temperature": 0.5, "final_accuracy": 0.87, "status": "completed"},
            {"seed": 2, "temperature": 0.7, "final_accuracy": 0.88, "status": "completed"},
            {"seed": 3, "temperature": 0.7, "final_accuracy": 0.90, "status": "completed"},
            {"seed": 4, "temperature": 0.9, "final_accuracy": 0.82, "status": "completed"},
            {"seed": 5, "temperature": 0.9, "final_accuracy": 0.84, "status": "completed"},
        ]
        
        report = compute_variance_metrics(results)
        
        assert len(report["variance_by_temperature"]) == 3
        assert "0.5" in report["variance_by_temperature"]
        assert "0.7" in report["variance_by_temperature"]
        assert "0.9" in report["variance_by_temperature"]
        
        # Check overall variance
        all_accuracies = [0.85, 0.87, 0.88, 0.90, 0.82, 0.84]
        expected_overall_var = float(sklearn_var(all_accuracies))
        assert abs(report["overall_variance"] - expected_overall_var) < 1e-6

    def test_compute_variance_metrics_with_failed_runs(self):
        """Test that failed runs are excluded from variance calculation."""
        results = [
            {"seed": 0, "temperature": 0.5, "final_accuracy": 0.85, "status": "completed"},
            {"seed": 1, "temperature": 0.5, "final_accuracy": None, "status": "failed", "error": "OOM"},
            {"seed": 2, "temperature": 0.5, "final_accuracy": 0.87, "status": "completed"},
        ]
        
        report = compute_variance_metrics(results)
        
        metrics = report["variance_by_temperature"]["0.5"]
        assert metrics["count"] == 2  # Only completed runs
        assert metrics["mean"] == pytest.approx(0.86, abs=0.01)

    def test_compute_variance_metrics_single_run_per_temp(self):
        """Test variance when only one run per temperature (variance should be 0)."""
        results = [
            {"seed": 0, "temperature": 0.5, "final_accuracy": 0.85, "status": "completed"},
            {"seed": 1, "temperature": 0.7, "final_accuracy": 0.88, "status": "completed"},
            {"seed": 2, "temperature": 0.9, "final_accuracy": 0.82, "status": "completed"},
        ]
        
        report = compute_variance_metrics(results)
        
        for temp in ["0.5", "0.7", "0.9"]:
            metrics = report["variance_by_temperature"][temp]
            assert metrics["count"] == 1
            assert metrics["variance"] == 0.0

    def test_variance_calculation_correctness(self):
        """Test that variance is calculated correctly using population variance."""
        accuracies = [0.80, 0.85, 0.90, 0.95]
        expected_var = float(sklearn_var(accuracies))
        
        results = [
            {"seed": i, "temperature": 0.5, "final_accuracy": acc, "status": "completed"}
            for i, acc in enumerate(accuracies)
        ]
        
        report = compute_variance_metrics(results)
        assert abs(report["variance_by_temperature"]["0.5"]["variance"] - expected_var) < 1e-6
        assert abs(report["overall_variance"] - expected_var) < 1e-6

    def test_report_structure(self):
        """Test that the variance report has the expected structure."""
        results = [
            {"seed": 0, "temperature": 0.5, "final_accuracy": 0.85, "status": "completed"},
            {"seed": 1, "temperature": 0.5, "final_accuracy": 0.87, "status": "completed"},
        ]
        
        report = compute_variance_metrics(results)
        
        assert "variance_by_temperature" in report
        assert "overall_variance" in report
        assert "overall_std" in report
        assert "total_completed_runs" in report
        assert "total_temperatures" in report
        
        assert isinstance(report["variance_by_temperature"], dict)
        assert isinstance(report["overall_variance"], float)
        assert isinstance(report["total_completed_runs"], int)