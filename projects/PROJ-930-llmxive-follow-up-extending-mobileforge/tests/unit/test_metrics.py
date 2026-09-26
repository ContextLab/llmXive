"""
Unit tests for utils.metrics module.
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
from pathlib import Path
import os
import json
import csv


class TestSuccessRateCalculator:
    def test_empty_list(self):
        calc = SuccessRateCalculator()
        result = calc.calculate([])
        assert result["success_rate"] == 0.0
        assert result["total_tasks"] == 0

    def test_all_success(self):
        results = [
            TaskResult("t1", True, 5),
            TaskResult("t2", True, 3)
        ]
        calc = SuccessRateCalculator()
        result = calc.calculate(results)
        assert result["success_rate"] == 1.0
        assert result["successful_tasks"] == 2

    def test_all_failure(self):
        results = [
            TaskResult("t1", False, 10),
            TaskResult("t2", False, 20)
        ]
        calc = SuccessRateCalculator()
        result = calc.calculate(results)
        assert result["success_rate"] == 0.0
        assert result["successful_tasks"] == 0

    def test_mixed(self):
        results = [
            TaskResult("t1", True, 5),
            TaskResult("t2", False, 10),
            TaskResult("t3", True, 8)
        ]
        calc = SuccessRateCalculator()
        result = calc.calculate(results)
        assert result["success_rate"] == 2/3
        assert result["failure_rate"] == 1/3


class TestStepEfficiencyCalculator:
    def test_empty_list(self):
        calc = StepEfficiencyCalculator()
        result = calc.calculate([])
        assert result["mean_efficiency"] == 0.0
        assert result["mean_steps"] == 0.0

    def test_no_max_steps(self):
        # Without max_steps, efficiency ratio cannot be calculated,
        # but mean steps should still work.
        results = [
            TaskResult("t1", True, 5),
            TaskResult("t2", True, 10)
        ]
        calc = StepEfficiencyCalculator()
        result = calc.calculate(results)
        # Efficiency should be 0.0 if no max_steps provided for normalization
        assert result["mean_efficiency"] == 0.0
        assert result["mean_steps"] == 7.5

    def test_with_max_steps(self):
        results = [
            TaskResult("t1", True, 5, max_steps=10), # Eff = 10/5 = 2.0
            TaskResult("t2", True, 10, max_steps=20) # Eff = 20/10 = 2.0
        ]
        calc = StepEfficiencyCalculator()
        result = calc.calculate(results)
        assert result["mean_efficiency"] == 2.0
        assert result["mean_steps"] == 7.5

    def test_mixed_success_failure(self):
        # Only successful tasks contribute to efficiency usually
        results = [
            TaskResult("t1", True, 5, max_steps=10),
            TaskResult("t2", False, 20, max_steps=20), # Failed, ignored
            TaskResult("t3", True, 10, max_steps=20)
        ]
        calc = StepEfficiencyCalculator()
        result = calc.calculate(results)
        # t1: 2.0, t3: 2.0 -> mean 2.0
        assert result["mean_efficiency"] == 2.0
        # Mean steps of successful: (5+10)/2 = 7.5
        assert result["mean_steps"] == 7.5

    def test_zero_steps_success(self):
        # Edge case: success with 0 steps?
        results = [
            TaskResult("t1", True, 0, max_steps=10)
        ]
        calc = StepEfficiencyCalculator()
        # __post_init__ allows 0 steps? Yes.
        # But efficiency calc filters r.steps > 0.
        result = calc.calculate(results)
        assert result["mean_efficiency"] == 0.0
        assert result["total_tasks_evaluated"] == 0


class TestMetricsReporter:
    def setup_method(self):
        self.tmp_dir = Path("tests/tmp_metrics")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.tmp_dir / "results.csv"

    def teardown_method(self):
        if self.output_file.exists():
            self.output_file.unlink()
        summary_file = self.tmp_dir / "results.json"
        if summary_file.exists():
            summary_file.unlink()
        if self.tmp_dir.exists():
            self.tmp_dir.rmdir()

    def test_add_results(self):
        reporter = MetricsReporter(str(self.output_file))
        r1 = TaskResult("t1", True, 5)
        r2 = TaskResult("t2", False, 10)
        reporter.add_results([r1, r2])
        assert len(reporter.results) == 2

    def test_write_csv(self):
        reporter = MetricsReporter(str(self.output_file))
        reporter.add_results([
            TaskResult("t1", True, 5, model_name="test_model"),
            TaskResult("t2", False, 10, model_name="test_model")
        ])
        reporter.write_csv()

        assert self.output_file.exists()
        with open(self.output_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['task_id', 'success', 'steps', 'model_name']
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0] == ['t1', 'True', '5', 'test_model']

    def test_write_summary(self):
        reporter = MetricsReporter(str(self.output_file))
        reporter.add_results([
            TaskResult("t1", True, 5, max_steps=10),
            TaskResult("t2", True, 10, max_steps=20)
        ])
        reporter.write_summary()

        summary_file = self.tmp_dir / "results.json"
        assert summary_file.exists()
        with open(summary_file, 'r') as f:
            data = json.load(f)
            assert "success_rate" in data
            assert "step_efficiency" in data
            assert data["success_rate"]["success_rate"] == 1.0


class TestConvenienceFunctions:
    def test_compute_success_rate(self):
        results = [
            TaskResult("t1", True, 5),
            TaskResult("t2", False, 10)
        ]
        assert compute_success_rate(results) == 0.5

    def test_compute_step_efficiency(self):
        results = [
            TaskResult("t1", True, 5, max_steps=10),
            TaskResult("t2", True, 10, max_steps=20)
        ]
        assert compute_step_efficiency(results) == 2.0