"""
Unit tests for the metrics calculation utilities.
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
    """Tests for the SuccessRateCalculator class."""
    
    def test_all_success(self):
        """Test success rate when all tasks succeed."""
        results = [
            TaskResult(task_id=f"t{i}", model_name="test", success=True, steps_taken=5)
            for i in range(10)
        ]
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        
        assert result["success_rate"] == 1.0
        assert result["successful_tasks"] == 10
        assert result["failed_tasks"] == 0
        assert result["total_tasks"] == 10
    
    def test_all_fail(self):
        """Test success rate when all tasks fail."""
        results = [
            TaskResult(task_id=f"t{i}", model_name="test", success=False, steps_taken=5)
            for i in range(10)
        ]
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        
        assert result["success_rate"] == 0.0
        assert result["successful_tasks"] == 0
        assert result["failed_tasks"] == 10
    
    def test_mixed_results(self):
        """Test success rate with mixed outcomes."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, steps_taken=5),
            TaskResult(task_id="t2", model_name="test", success=False, steps_taken=5),
            TaskResult(task_id="t3", model_name="test", success=True, steps_taken=5),
            TaskResult(task_id="t4", model_name="test", success=False, steps_taken=5),
            TaskResult(task_id="t5", model_name="test", success=True, steps_taken=5),
        ]
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        
        assert result["success_rate"] == 0.6
        assert result["successful_tasks"] == 3
        assert result["failed_tasks"] == 2
    
    def test_insufficient_samples(self):
        """Test that insufficient samples raise an error."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, steps_taken=5)
        ]
        calculator = SuccessRateCalculator(min_samples=5)
        
        with pytest.raises(ValueError, match="Insufficient samples"):
            calculator.calculate(results)


class TestStepEfficiencyCalculator:
    """Tests for the StepEfficiencyCalculator class."""
    
    def test_perfect_efficiency(self):
        """Test efficiency when actual steps equal optimal steps."""
        results = [
            TaskResult(task_id=f"t{i}", model_name="test", success=True, 
                     steps_taken=5, steps_optimal=5)
            for i in range(10)
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        
        assert result["step_efficiency"] == 1.0
        assert result["total_steps_taken"] == 50
        assert result["total_optimal_steps"] == 50
    
    def test_suboptimal_efficiency(self):
        """Test efficiency when actual steps exceed optimal steps."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t2", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        
        # Total optimal: 10, Total actual: 20 -> Efficiency: 0.5
        assert result["step_efficiency"] == 0.5
        assert result["total_steps_taken"] == 20
        assert result["total_optimal_steps"] == 10
    
    def test_mixed_optimal_unknown(self):
        """Test efficiency calculation ignores tasks without optimal steps."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t2", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t3", model_name="test", success=True, 
                     steps_taken=20, steps_optimal=None),  # Should be ignored
        ]
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        
        # Only t1 and t2 count: optimal=10, actual=20 -> 0.5
        assert result["step_efficiency"] == 0.5
        assert result["samples_with_optimal"] == 2
        assert result["samples_without_optimal"] == 1
    
    def test_insufficient_samples_with_optimal(self):
        """Test error when insufficient samples have optimal steps."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, 
                     steps_taken=5, steps_optimal=5),
            TaskResult(task_id="t2", model_name="test", success=True, 
                     steps_taken=5, steps_optimal=None),
        ]
        calculator = StepEfficiencyCalculator(min_samples_with_optimal=2)
        
        with pytest.raises(ValueError, match="Insufficient samples with optimal steps"):
            calculator.calculate(results)


class TestMetricsReporter:
    """Tests for the MetricsReporter class."""
    
    def test_generate_report(self):
        """Test report generation with mixed results."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t2", model_name="test", success=False, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t3", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
        ]
        reporter = MetricsReporter()
        report = reporter.generate_report(results)
        
        assert report["total_results"] == 3
        assert "success_rate" in report["metrics"]
        assert "step_efficiency" in report["metrics"]
        assert report["metrics"]["success_rate"]["success_rate"] == 2/3
        assert report["metrics"]["step_efficiency"]["step_efficiency"] == 0.5
    
    def test_write_report_to_csv(self, tmp_path):
        """Test writing results to CSV file."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t2", model_name="test", success=False, 
                     steps_taken=10, steps_optimal=5),
        ]
        output_file = tmp_path / "metrics_report.csv"
        reporter = MetricsReporter()
        reporter.write_report_to_csv(results, str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "t1" in content
        assert "t2" in content
        assert "success_rate" in content
        assert "step_efficiency" in content


class TestConvenienceFunctions:
    """Tests for the convenience functions."""
    
    def test_compute_success_rate(self):
        """Test the compute_success_rate function."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, steps_taken=5),
            TaskResult(task_id="t2", model_name="test", success=False, steps_taken=5),
            TaskResult(task_id="t3", model_name="test", success=True, steps_taken=5),
        ]
        rate = compute_success_rate(results)
        assert rate == 2/3
    
    def test_compute_step_efficiency(self):
        """Test the compute_step_efficiency function."""
        results = [
            TaskResult(task_id="t1", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
            TaskResult(task_id="t2", model_name="test", success=True, 
                     steps_taken=10, steps_optimal=5),
        ]
        efficiency = compute_step_efficiency(results)
        assert efficiency == 0.5