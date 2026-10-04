"""
Metrics calculation utilities for MobileForge logic distillation evaluation.

This module provides base classes and implementations for calculating
Success Rate and Step Efficiency metrics, as required by the evaluation pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import csv
import os
from pathlib import Path


@dataclass
class TaskResult:
    """
    Represents the outcome of a single task execution.
    
    Attributes:
        task_id: Unique identifier for the task
        model_name: Name of the model that executed the task
        success: Boolean indicating if the task was completed successfully
        steps_taken: Number of steps taken to complete the task (or attempt)
        max_steps: Maximum allowed steps for the task
        timestamp: Optional timestamp of execution
        metadata: Additional context about the execution
    """
    task_id: str
    model_name: str
    success: bool
    steps_taken: int
    max_steps: int
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricCalculator(ABC):
    """
    Abstract base class for metric calculators.
    
    Provides the interface for all metric calculation operations.
    """
    
    @abstractmethod
    def calculate(self, results: List[TaskResult]) -> Dict[str, Any]:
        """
        Calculate the metric from a list of task results.
        
        Args:
            results: List of TaskResult objects to analyze
            
        Returns:
            Dictionary containing the calculated metric(s)
        """
        pass

class SuccessRateCalculator(MetricCalculator):
    """
    Calculator for Success Rate metric.
    
    Success Rate = (Number of successful tasks) / (Total number of tasks)
    
    This metric measures the proportion of tasks that were completed
    successfully by a model.
    """
    
    def calculate(self, results: List[TaskResult]) -> Dict[str, Any]:
        """
        Calculate success rate from task results.
        
        Args:
            results: List of TaskResult objects
            
        Returns:
            Dictionary with 'success_rate' (float), 'successful_count' (int),
            'total_count' (int), and 'failed_count' (int)
        """
        if not results:
            return {
                'success_rate': 0.0,
                'successful_count': 0,
                'total_count': 0,
                'failed_count': 0
            }
        
        successful_count = sum(1 for r in results if r.success)
        total_count = len(results)
        failed_count = total_count - successful_count
        success_rate = successful_count / total_count if total_count > 0 else 0.0
        
        return {
            'success_rate': success_rate,
            'successful_count': successful_count,
            'total_count': total_count,
            'failed_count': failed_count
        }

class StepEfficiencyCalculator(MetricCalculator):
    """
    Calculator for Step Efficiency metric.
    
    Step Efficiency = (Average steps taken by successful tasks) / (Average max_steps)
    
    This metric measures how efficiently a model completes tasks relative to
    the maximum allowed steps. Lower values indicate better efficiency
    (fewer steps needed to complete tasks).
    
    Only successful tasks are considered for step efficiency calculation.
    """
    
    def calculate(self, results: List[TaskResult]) -> Dict[str, Any]:
        """
        Calculate step efficiency from task results.
        
        Args:
            results: List of TaskResult objects
            
        Returns:
            Dictionary with 'step_efficiency' (float), 'avg_steps_taken' (float),
            'avg_max_steps' (float), and 'successful_count' (int)
        """
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {
                'step_efficiency': 0.0,
                'avg_steps_taken': 0.0,
                'avg_max_steps': 0.0,
                'successful_count': 0
            }
        
        total_steps_taken = sum(r.steps_taken for r in successful_results)
        total_max_steps = sum(r.max_steps for r in successful_results)
        successful_count = len(successful_results)
        
        avg_steps_taken = total_steps_taken / successful_count
        avg_max_steps = total_max_steps / successful_count
        
        # Efficiency: lower is better (fewer steps relative to max allowed)
        # Normalized to [0, 1] where 1 means always used max steps, 0 means instant
        step_efficiency = avg_steps_taken / avg_max_steps if avg_max_steps > 0 else 0.0
        
        return {
            'step_efficiency': step_efficiency,
            'avg_steps_taken': avg_steps_taken,
            'avg_max_steps': avg_max_steps,
            'successful_count': successful_count
        }

class MetricsReporter:
    """
    Utility class for generating and exporting metrics reports.
    
    Handles aggregation of multiple metric calculators and output formatting.
    """
    
    def __init__(self):
        self.calculators: Dict[str, MetricCalculator] = {}
        self.results: List[TaskResult] = []
    
    def add_calculator(self, name: str, calculator: MetricCalculator) -> None:
        """
        Register a metric calculator.
        
        Args:
            name: Identifier for the calculator
            calculator: Instance of MetricCalculator
        """
        self.calculators[name] = calculator
    
    def set_results(self, results: List[TaskResult]) -> None:
        """
        Set the task results to be analyzed.
        
        Args:
            results: List of TaskResult objects
        """
        self.results = results
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive metrics report.
        
        Returns:
            Dictionary containing all calculated metrics
        """
        report = {
            'total_tasks': len(self.results),
            'metrics': {}
        }
        
        for name, calculator in self.calculators.items():
            report['metrics'][name] = calculator.calculate(self.results)
        
        return report
    
    def write_csv_report(self, output_path: str, results: Optional[List[TaskResult]] = None) -> Path:
        """
        Write task results to a CSV file.
        
        Args:
            output_path: Path to the output CSV file
            results: Optional list of results (uses self.results if not provided)
            
        Returns:
            Path to the created file
        """
        if results is None:
            results = self.results
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'task_id', 'model_name', 'success', 'steps_taken', 
            'max_steps', 'timestamp'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'task_id': result.task_id,
                    'model_name': result.model_name,
                    'success': result.success,
                    'steps_taken': result.steps_taken,
                    'max_steps': result.max_steps,
                    'timestamp': result.timestamp or ''
                })
        
        return output_path
    
    def write_json_report(self, output_path: str) -> Path:
        """
        Write metrics report to a JSON file.
        
        Args:
            output_path: Path to the output JSON file
            
        Returns:
            Path to the created file
        """
        import json
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return output_path

def compute_success_rate(results: List[TaskResult]) -> float:
    """
    Convenience function to compute success rate.
    
    Args:
        results: List of TaskResult objects
        
    Returns:
        Success rate as a float between 0.0 and 1.0
    """
    calculator = SuccessRateCalculator()
    return calculator.calculate(results)['success_rate']

def compute_step_efficiency(results: List[TaskResult]) -> float:
    """
    Convenience function to compute step efficiency.
    
    Args:
        results: List of TaskResult objects
        
    Returns:
        Step efficiency as a float between 0.0 and 1.0
    """
    calculator = StepEfficiencyCalculator()
    return calculator.calculate(results)['step_efficiency']
