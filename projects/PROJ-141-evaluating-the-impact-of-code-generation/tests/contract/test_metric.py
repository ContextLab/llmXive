"""
Contract test for Metric schema (US2).

Validates that the Metric dataclass from code/data/models.py
satisfies the schema requirements for the quality assessment pipeline.

Tests verify:
1. Required fields exist and have correct types
2. Metric values are within expected ranges
3. Schema matches data-model.md specifications
"""

import pytest
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.models import Metric, Condition, ProblemSource
from dataclasses import fields


class TestMetricSchema:
    """Contract tests for Metric schema."""

    def test_metric_has_required_fields(self):
        """Verify Metric has all required fields per data-model.md."""
        field_names = {f.name for f in fields(Metric)}
        
        required_fields = {
            'submission_id',
            'condition',
            'problem_id',
            'pass_rate',
            'cyclomatic_complexity',
            'test_coverage',
            'static_analysis_warnings',
            'timestamp'
        }
        
        missing = required_fields - field_names
        assert not missing, f"Missing required fields: {missing}"

    def test_metric_field_types(self):
        """Verify each field has the correct type."""
        expected_types = {
            'submission_id': str,
            'condition': Condition,
            'problem_id': str,
            'pass_rate': float,
            'cyclomatic_complexity': int,
            'test_coverage': float,
            'static_analysis_warnings': int,
            'timestamp': datetime
        }
        
        metric_fields = {f.name: f.type for f in fields(Metric)}
        
        for field_name, expected_type in expected_types.items():
            assert field_name in metric_fields, f"Field {field_name} not found"
            # For Enum types, check the base class
            if expected_type == Condition:
                assert metric_fields[field_name].__name__ == 'Condition' or \
                       metric_fields[field_name] == Condition
            else:
                assert metric_fields[field_name] == expected_type, \
                    f"Field {field_name} has type {metric_fields[field_name]}, expected {expected_type}"

    def test_metric_pass_rate_range(self):
        """Verify pass_rate is between 0.0 and 1.0 with ≥0.01 precision."""
        # Create a valid Metric instance
        metric = Metric(
            submission_id="test-submission-001",
            condition=Condition.LLM_ASSISTED,
            problem_id="HumanEval/0",
            pass_rate=0.85,
            cyclomatic_complexity=5,
            test_coverage=75.5,
            static_analysis_warnings=2,
            timestamp=datetime.now()
        )
        
        assert 0.0 <= metric.pass_rate <= 1.0, \
            f"pass_rate {metric.pass_rate} must be between 0.0 and 1.0"

    def test_metric_cyclomatic_complexity_minimum(self):
        """Verify cyclomatic_complexity is an integer ≥1."""
        metric = Metric(
            submission_id="test-submission-002",
            condition=Condition.BASELINE,
            problem_id="Codeforces/123",
            pass_rate=0.5,
            cyclomatic_complexity=1,
            test_coverage=50.0,
            static_analysis_warnings=0,
            timestamp=datetime.now()
        )
        
        assert isinstance(metric.cyclomatic_complexity, int), \
            f"cyclomatic_complexity must be int, got {type(metric.cyclomatic_complexity)}"
        assert metric.cyclomatic_complexity >= 1, \
            f"cyclomatic_complexity must be ≥1, got {metric.cyclomatic_complexity}"

    def test_metric_test_coverage_range(self):
        """Verify test_coverage is between 0 and 100."""
        metric = Metric(
            submission_id="test-submission-003",
            condition=Condition.LLM_ASSISTED,
            problem_id="HumanEval/5",
            pass_rate=1.0,
            cyclomatic_complexity=3,
            test_coverage=100.0,
            static_analysis_warnings=0,
            timestamp=datetime.now()
        )
        
        assert 0.0 <= metric.test_coverage <= 100.0, \
            f"test_coverage {metric.test_coverage} must be between 0 and 100"

    def test_metric_static_analysis_warnings_minimum(self):
        """Verify static_analysis_warnings is a non-negative integer."""
        metric = Metric(
            submission_id="test-submission-004",
            condition=Condition.BASELINE,
            problem_id="Codeforces/456",
            pass_rate=0.0,
            cyclomatic_complexity=10,
            test_coverage=0.0,
            static_analysis_warnings=0,
            timestamp=datetime.now()
        )
        
        assert isinstance(metric.static_analysis_warnings, int), \
            f"static_analysis_warnings must be int, got {type(metric.static_analysis_warnings)}"
        assert metric.static_analysis_warnings >= 0, \
            f"static_analysis_warnings must be ≥0, got {metric.static_analysis_warnings}"

    def test_metric_condition_enum_values(self):
        """Verify condition field accepts valid Condition enum values."""
        valid_conditions = [Condition.LLM_ASSISTED, Condition.BASELINE]
        
        for condition in valid_conditions:
            metric = Metric(
                submission_id=f"test-submission-{condition.value}",
                condition=condition,
                problem_id="HumanEval/0",
                pass_rate=0.5,
                cyclomatic_complexity=2,
                test_coverage=50.0,
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )
            assert metric.condition == condition, \
                f"Condition {condition} not properly assigned"

    def test_metric_problem_id_format(self):
        """Verify problem_id follows expected format (Source/ID)."""
        test_ids = [
            "HumanEval/0",
            "HumanEval/123",
            "Codeforces/1001",
            "Codeforces/999999"
        ]
        
        for problem_id in test_ids:
            metric = Metric(
                submission_id="test-submission-format",
                condition=Condition.LLM_ASSISTED,
                problem_id=problem_id,
                pass_rate=0.5,
                cyclomatic_complexity=2,
                test_coverage=50.0,
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )
            assert metric.problem_id == problem_id
            assert "/" in problem_id, f"problem_id {problem_id} must contain '/'"

    def test_metric_timestamp_format(self):
        """Verify timestamp is a datetime object."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        metric = Metric(
            submission_id="test-submission-timestamp",
            condition=Condition.BASELINE,
            problem_id="HumanEval/0",
            pass_rate=0.75,
            cyclomatic_complexity=4,
            test_coverage=60.0,
            static_analysis_warnings=3,
            timestamp=timestamp
        )
        
        assert isinstance(metric.timestamp, datetime), \
            f"timestamp must be datetime, got {type(metric.timestamp)}"
        assert metric.timestamp == timestamp

    def test_metric_to_dict_serialization(self):
        """Verify Metric can be serialized to dict for storage."""
        metric = Metric(
            submission_id="test-submission-serialize",
            condition=Condition.LLM_ASSISTED,
            problem_id="HumanEval/10",
            pass_rate=0.92,
            cyclomatic_complexity=6,
            test_coverage=85.5,
            static_analysis_warnings=1,
            timestamp=datetime(2024, 1, 15, 14, 20, 30)
        )
        
        # Convert to dict (using dataclasses.asdict if needed, or custom)
        from dataclasses import asdict
        metric_dict = asdict(metric)
        
        assert isinstance(metric_dict, dict)
        assert metric_dict['submission_id'] == "test-submission-serialize"
        assert metric_dict['condition'] == "LLM_ASSISTED"
        assert metric_dict['problem_id'] == "HumanEval/10"
        assert metric_dict['pass_rate'] == 0.92
        assert metric_dict['cyclomatic_complexity'] == 6
        assert metric_dict['test_coverage'] == 85.5
        assert metric_dict['static_analysis_warnings'] == 1
        assert isinstance(metric_dict['timestamp'], datetime)

    def test_metric_from_dict_deserialization(self):
        """Verify Metric can be created from dict."""
        metric_dict = {
            'submission_id': 'test-submission-deserialize',
            'condition': Condition.BASELINE,
            'problem_id': 'Codeforces/789',
            'pass_rate': 0.65,
            'cyclomatic_complexity': 8,
            'test_coverage': 45.0,
            'static_analysis_warnings': 5,
            'timestamp': datetime(2024, 1, 16, 9, 15, 45)
        }
        
        metric = Metric(**metric_dict)
        
        assert metric.submission_id == metric_dict['submission_id']
        assert metric.condition == metric_dict['condition']
        assert metric.problem_id == metric_dict['problem_id']
        assert metric.pass_rate == metric_dict['pass_rate']
        assert metric.cyclomatic_complexity == metric_dict['cyclomatic_complexity']
        assert metric.test_coverage == metric_dict['test_coverage']
        assert metric.static_analysis_warnings == metric_dict['static_analysis_warnings']
        assert metric.timestamp == metric_dict['timestamp']

    def test_metric_validation_rejects_invalid_pass_rate(self):
        """Verify Metric rejects pass_rate outside [0.0, 1.0]."""
        with pytest.raises(AssertionError):
            Metric(
                submission_id="invalid-pass-rate",
                condition=Condition.LLM_ASSISTED,
                problem_id="HumanEval/0",
                pass_rate=1.5,  # Invalid: > 1.0
                cyclomatic_complexity=2,
                test_coverage=50.0,
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )

        with pytest.raises(AssertionError):
            Metric(
                submission_id="invalid-pass-rate-negative",
                condition=Condition.BASELINE,
                problem_id="HumanEval/0",
                pass_rate=-0.1,  # Invalid: < 0.0
                cyclomatic_complexity=2,
                test_coverage=50.0,
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )

    def test_metric_validation_rejects_invalid_complexity(self):
        """Verify Metric rejects cyclomatic_complexity < 1."""
        with pytest.raises(AssertionError):
            Metric(
                submission_id="invalid-complexity",
                condition=Condition.LLM_ASSISTED,
                problem_id="HumanEval/0",
                pass_rate=0.5,
                cyclomatic_complexity=0,  # Invalid: < 1
                test_coverage=50.0,
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )

    def test_metric_validation_rejects_invalid_coverage(self):
        """Verify Metric rejects test_coverage outside [0, 100]."""
        with pytest.raises(AssertionError):
            Metric(
                submission_id="invalid-coverage",
                condition=Condition.BASELINE,
                problem_id="HumanEval/0",
                pass_rate=0.5,
                cyclomatic_complexity=2,
                test_coverage=105.0,  # Invalid: > 100
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )

        with pytest.raises(AssertionError):
            Metric(
                submission_id="invalid-coverage-negative",
                condition=Condition.BASELINE,
                problem_id="HumanEval/0",
                pass_rate=0.5,
                cyclomatic_complexity=2,
                test_coverage=-5.0,  # Invalid: < 0
                static_analysis_warnings=1,
                timestamp=datetime.now()
            )

    def test_metric_validation_rejects_negative_warnings(self):
        """Verify Metric rejects negative static_analysis_warnings."""
        with pytest.raises(AssertionError):
            Metric(
                submission_id="invalid-warnings",
                condition=Condition.LLM_ASSISTED,
                problem_id="HumanEval/0",
                pass_rate=0.5,
                cyclomatic_complexity=2,
                test_coverage=50.0,
                static_analysis_warnings=-1,  # Invalid: < 0
                timestamp=datetime.now()
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
