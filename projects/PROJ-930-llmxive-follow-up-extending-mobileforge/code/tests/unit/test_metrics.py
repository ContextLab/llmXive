"""
Unit tests for metrics calculation utilities.
"""
import pytest
from utils.metrics import (
    TaskResult,
    MetricCalculator,
    SuccessRateCalculator,
    StepEfficiencyCalculator,
    MetricsReporter,
    compute_success_rate,
    compute_step_efficiency
)


class TestSuccessRateCalculator:
    """Tests for the SuccessRateCalculator class."""
    
    def test_empty_results(self):
        """Test calculation with empty results list."""
        calculator = SuccessRateCalculator()
        result = calculator.calculate([])
        
        assert result['success_rate'] == 0.0
        assert result['successful_count'] == 0
        assert result['total_count'] == 0
        assert result['failed_count'] == 0
    
    def test_all_success(self):
        """Test calculation when all tasks succeed."""
        results = [
            TaskResult(task_id=f"task_{i}", model_name="test", success=True, 
                     steps_taken=5, max_steps=10)
            for i in range(5)
        ]
        
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        
        assert result['success_rate'] == 1.0
        assert result['successful_count'] == 5
        assert result['total_count'] == 5
        assert result['failed_count'] == 0
    
    def test_all_fail(self):
        """Test calculation when all tasks fail."""
        results = [
            TaskResult(task_id=f"task_{i}", model_name="test", success=False,
                     steps_taken=10, max_steps=10)
            for i in range(5)
        ]
        
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        
        assert result['success_rate'] == 0.0
        assert result['successful_count'] == 0
        assert result['total_count'] == 5
        assert result['failed_count'] == 5
    
    def test_mixed_results(self):
        """Test calculation with mixed success/failure."""
        results = [
            TaskResult(task_id="task_1", model_name="test", success=True,
                     steps_taken=5, max_steps=10),
            TaskResult(task_id="task_2", model_name="test", success=False,
                     steps_taken=10, max_steps=10),
            TaskResult(task_id="task_3", model_name="test", success=True,
                     steps_taken=3, max_steps=10),
            TaskResult(task_id="task_4", model_name="test", success=False,
                     steps_taken=8, max_steps=10),
        ]
        
        calculator = SuccessRateCalculator()
        result = calculator.calculate(results)
        
        assert result['success_rate'] == 0.5
        assert result['successful_count'] == 2
        assert result['total_count'] == 4
        assert result['failed_count'] == 2


class TestStepEfficiencyCalculator:
    """Tests for the StepEfficiencyCalculator class."""
    
    def test_empty_results(self):
        """Test calculation with empty results list."""
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate([])
        
        assert result['step_efficiency'] == 0.0
        assert result['avg_steps_taken'] == 0.0
        assert result['avg_max_steps'] == 0.0
        assert result['successful_count'] == 0
    
    def test_no_successful_tasks(self):
        """Test calculation when no tasks succeed."""
        results = [
            TaskResult(task_id=f"task_{i}", model_name="test", success=False,
                     steps_taken=10, max_steps=10)
            for i in range(3)
        ]
        
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        
        assert result['step_efficiency'] == 0.0
        assert result['successful_count'] == 0
    
    def test_all_successful_same_steps(self):
        """Test calculation when all tasks succeed with same steps."""
        results = [
            TaskResult(task_id=f"task_{i}", model_name="test", success=True,
                     steps_taken=5, max_steps=10)
            for i in range(3)
        ]
        
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        
        assert result['step_efficiency'] == 0.5  # 5/10
        assert result['avg_steps_taken'] == 5.0
        assert result['avg_max_steps'] == 10.0
        assert result['successful_count'] == 3
    
    def test_successful_tasks_different_steps(self):
        """Test calculation with successful tasks taking different steps."""
        results = [
            TaskResult(task_id="task_1", model_name="test", success=True,
                     steps_taken=2, max_steps=10),
            TaskResult(task_id="task_2", model_name="test", success=True,
                     steps_taken=4, max_steps=10),
            TaskResult(task_id="task_3", model_name="test", success=True,
                     steps_taken=6, max_steps=10),
        ]
        
        calculator = StepEfficiencyCalculator()
        result = calculator.calculate(results)
        
        # Average steps = (2+4+6)/3 = 4
        # Efficiency = 4/10 = 0.4
        assert result['step_efficiency'] == 0.4
        assert result['avg_steps_taken'] == 4.0
        assert result['successful_count'] == 3


class TestMetricsReporter:
    """Tests for the MetricsReporter class."""
    
    def test_add_calculator(self):
        """Test adding calculators to the reporter."""
        reporter = MetricsReporter()
        success_calc = SuccessRateCalculator()
        efficiency_calc = StepEfficiencyCalculator()
        
        reporter.add_calculator('success_rate', success_calc)
        reporter.add_calculator('step_efficiency', efficiency_calc)
        
        assert 'success_rate' in reporter.calculators
        assert 'step_efficiency' in reporter.calculators
    
    def test_generate_report(self):
        """Test generating a full report."""
        results = [
            TaskResult(task_id="task_1", model_name="test", success=True,
                     steps_taken=5, max_steps=10),
            TaskResult(task_id="task_2", model_name="test", success=False,
                     steps_taken=10, max_steps=10),
        ]
        
        reporter = MetricsReporter()
        reporter.add_calculator('success_rate', SuccessRateCalculator())
        reporter.add_calculator('step_efficiency', StepEfficiencyCalculator())
        reporter.set_results(results)
        
        report = reporter.generate_report()
        
        assert 'total_tasks' in report
        assert 'metrics' in report
        assert 'success_rate' in report['metrics']
        assert 'step_efficiency' in report['metrics']
        assert report['total_tasks'] == 2


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_compute_success_rate(self):
        """Test the compute_success_rate convenience function."""
        results = [
            TaskResult(task_id="task_1", model_name="test", success=True,
                     steps_taken=5, max_steps=10),
            TaskResult(task_id="task_2", model_name="test", success=False,
                     steps_taken=10, max_steps=10),
        ]
        
        rate = compute_success_rate(results)
        assert rate == 0.5
    
    def test_compute_step_efficiency(self):
        """Test the compute_step_efficiency convenience function."""
        results = [
            TaskResult(task_id="task_1", model_name="test", success=True,
                     steps_taken=5, max_steps=10),
            TaskResult(task_id="task_2", model_name="test", success=True,
                     steps_taken=5, max_steps=10),
        ]
        
        efficiency = compute_step_efficiency(results)
        assert efficiency == 0.5