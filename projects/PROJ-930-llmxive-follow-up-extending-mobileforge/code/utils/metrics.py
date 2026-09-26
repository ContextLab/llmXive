"""
Metrics module for calculating Success Rate and Step Efficiency.

This module provides base classes and concrete implementations for evaluating
model performance on Android automation tasks.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import csv
import os
from pathlib import Path


@dataclass
class TaskResult:
    """Container for the result of a single task execution."""
    task_id: str
    success: bool
    steps_taken: int
    steps_optimal: int
    model_name: str
    error_message: Optional[str] = None
    
    def step_efficiency(self) -> float:
        """Calculate step efficiency: optimal_steps / actual_steps."""
        if self.steps_taken == 0:
            return 0.0
        if self.steps_optimal == 0:
            return 0.0
        return self.steps_optimal / self.steps_taken


class MetricCalculator(ABC):
    """Abstract base class for metric calculators."""
    
    @abstractmethod
    def calculate(self, results: List[TaskResult]) -> Dict[str, Any]:
        """Calculate the metric from a list of TaskResults."""
        pass


class SuccessRateCalculator(MetricCalculator):
    """Calculates the success rate (percentage of successful tasks)."""
    
    def calculate(self, results: List[TaskResult]) -> Dict[str, Any]:
        if not results:
            return {
                "success_rate": 0.0,
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0
            }
        
        successful = sum(1 for r in results if r.success)
        total = len(results)
        
        return {
            "success_rate": successful / total,
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": total - successful
        }


class StepEfficiencyCalculator(MetricCalculator):
    """Calculates the average step efficiency across tasks."""
    
    def calculate(self, results: List[TaskResult]) -> Dict[str, Any]:
        if not results:
            return {
                "mean_efficiency": 0.0,
                "total_tasks": 0,
                "efficiencies": []
            }
        
        efficiencies = [r.step_efficiency() for r in results]
        
        return {
            "mean_efficiency": sum(efficiencies) / len(efficiencies),
            "total_tasks": len(results),
            "efficiencies": efficiencies,
            "min_efficiency": min(efficiencies),
            "max_efficiency": max(efficiencies)
        }


class MetricsReporter:
    """Aggregates metrics from multiple calculators and reports them."""
    
    def __init__(self):
        self.calculators: Dict[str, MetricCalculator] = {
            "success_rate": SuccessRateCalculator(),
            "step_efficiency": StepEfficiencyCalculator()
        }
    
    def add_calculator(self, name: str, calculator: MetricCalculator) -> None:
        """Add a custom calculator."""
        self.calculators[name] = calculator
    
    def report(self, results: List[TaskResult]) -> Dict[str, Any]:
        """Generate a full report for the given results."""
        report = {
            "total_tasks": len(results),
            "metrics": {}
        }
        
        for name, calculator in self.calculators.items():
            report["metrics"][name] = calculator.calculate(results)
        
        return report
    
    def to_csv(self, results: List[TaskResult], output_path: str) -> None:
        """Write individual task results to a CSV file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'task_id', 'success', 'steps_taken', 'steps_optimal', 
                'model_name', 'error_message', 'step_efficiency'
            ])
            writer.writeheader()
            
            for r in results:
                writer.writerow({
                    'task_id': r.task_id,
                    'success': r.success,
                    'steps_taken': r.steps_taken,
                    'steps_optimal': r.steps_optimal,
                    'model_name': r.model_name,
                    'error_message': r.error_message or '',
                    'step_efficiency': r.step_efficiency()
                })


# Convenience functions for direct usage
def compute_success_rate(results: List[TaskResult]) -> float:
    """Compute success rate from a list of TaskResults."""
    calculator = SuccessRateCalculator()
    return calculator.calculate(results)["success_rate"]


def compute_step_efficiency(results: List[TaskResult]) -> float:
    """Compute mean step efficiency from a list of TaskResults."""
    calculator = StepEfficiencyCalculator()
    return calculator.calculate(results)["mean_efficiency"]
