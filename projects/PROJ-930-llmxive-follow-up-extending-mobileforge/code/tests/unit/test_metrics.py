"""
Unit tests for the metrics module.
"""
import pytest
from utils.metrics import (
    TaskResult,
    SuccessRateCalculator,
    StepEfficiencyCalculator,
    MetricsReporter,
    compute_success_rate,
    compute_step_efficiency
)


class TestSuccessRateCalculator:
    """Tests for SuccessRateCalculator."""
    
    def test_empty_results(self):
        """Test calculation with empty results."""
        calculator = SuccessRateCalculator()
        result = calculator.calculate([])
        assert result["success_rate"] == 0.0
        assert result["total_tasks"] == 0
        assert result["successful_tasks"] == 0
    
    def test_all_success(self):
        """Test calculation when all tasks succeed."""
        results = [
            TaskResult("t1", True, 5, 5, "model"),
            TaskResult("t2", True, 3, 3, "model"),
            TaskResult("t3", True, 10, 10, "model")
        ]
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        assert result["success_rate"] == 1.0
        assert result["successful_tasks"] == 3
    
    def test_all_failure(self):
        """Test calculation when all tasks fail."""
        results = [
            TaskResult("t1", False, 0, 5, "model"),
            TaskResult("t2", False, 0, 3, "model")
        ]
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        assert result["success_rate"] == 0.0
        assert result["successful_tasks"] == 0
    
    def test_mixed_results(self):
        """Test calculation with mixed success/failure."""
        results = [
            TaskResult("t1", True, 5, 5, "model"),
            TaskResult("t2", False, 0, 3, "model"),
            TaskResult("t3", True, 10, 10, "model"),
            TaskResult("t4", False, 0, 2, "model")
        ]
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        assert result["success_rate"] == 0.5
        assert result["successful_tasks"] == 2
        assert result["failed_tasks"] == 2


class TestStepEfficiencyCalculator:
    """Tests for StepEfficiencyCalculator."""
    
    def test_empty_results(self):
        """Test calculation with empty results."""
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate([])
        assert result["mean_efficiency"] == 0.0
        assert result["total_tasks"] == 0
    
    def test_perfect_efficiency(self):
        """Test calculation when all tasks have perfect efficiency."""
        results = [
            TaskResult("t1", True, 5, 5, "model"),
            TaskResult("t2", True, 3, 3, "model")
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        assert result["mean_efficiency"] == 1.0
    
    def test_zero_efficiency(self):
        """Test calculation when steps taken is zero (failed tasks)."""
        results = [
            TaskResult("t1", False, 0, 5, "model"),
            TaskResult("t2", False, 0, 3, "model")
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        assert result["mean_efficiency"] == 0.0
    
    def test_partial_efficiency(self):
        """Test calculation with partial efficiency."""
        results = [
            TaskResult("t1", True, 10, 5, "model"),  # 0.5 efficiency
            TaskResult("t2", True, 6, 3, "model")    # 0.5 efficiency
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        assert result["mean_efficiency"] == 0.5
    
    def test_mixed_efficiency(self):
        """Test calculation with mixed efficiencies."""
        results = [
            TaskResult("t1", True, 5, 5, "model"),   # 1.0
            TaskResult("t2", True, 10, 5, "model"),  # 0.5
            TaskResult("t3", True, 15, 5, "model")   # 0.333...
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        expected = (1.0 + 0.5 + (5/15)) / 3
        assert abs(result["mean_efficiency"] - expected) < 1e-6
        assert result["min_efficiency"] == 5/15
        assert result["max_efficiency"] == 1.0


class TestMetricsReporter:
    """Tests for MetricsReporter."""
    
    def test_generate_report(self):
        """Test generating a full report."""
        results = [
            TaskResult("t1", True, 5, 5, "model"),
            TaskResult("t2", False, 0, 5, "model")
        ]
        reporter = MetricsReporter()
        report = reporter.report(results)
        
        assert report["total_tasks"] == 2
        assert "success_rate" in report["metrics"]
        assert "step_efficiency" in report["metrics"]
        assert report["metrics"]["success_rate"]["success_rate"] == 0.5
    
    def test_add_custom_calculator(self):
        """Test adding a custom calculator."""
        from utils.metrics import MetricCalculator
        
        class DummyCalculator(MetricCalculator):
            def calculate(self, results):
                return {"dummy": 42}
        
        reporter = MetricsReporter()
        reporter.add_calculator("dummy_metric", DummyCalculator())
        
        results = [TaskResult("t1", True, 5, 5, "model")]
        report = reporter.report(results)
        
        assert "dummy_metric" in report["metrics"]
        assert report["metrics"]["dummy_metric"]["dummy"] == 42


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_compute_success_rate(self):
        """Test compute_success_rate function."""
        results = [
            TaskResult("t1", True, 5, 5, "model"),
            TaskResult("t2", False, 0, 5, "model")
        ]
        rate = compute_success_rate(results)
        assert rate == 0.5
    
    def test_compute_step_efficiency(self):
        """Test compute_step_efficiency function."""
        results = [
            TaskResult("t1", True, 10, 5, "model"),
            TaskResult("t2", True, 10, 5, "model")
        ]
        efficiency = compute_step_efficiency(results)
        assert efficiency == 0.5