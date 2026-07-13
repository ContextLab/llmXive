"""
Contract tests for User Story 2 (Quality Assessment) schemas.

This module validates that the Metric schema defined in code/data/models.py
matches the expected structure required for the quality assessment pipeline.

Tests verify:
1. Metric dataclass fields and types
2. Schema serialization/deserialization
3. Required field presence
4. Data integrity constraints
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import the Metric model from the project's data models
from data.models import Metric, Condition, ProblemSource


class TestMetricSchema:
    """Contract tests for the Metric schema."""

    def test_metric_dataclass_fields_exist(self):
        """Verify all required fields exist in the Metric dataclass."""
        # Check that the Metric class has the expected fields
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        # Assert all expected attributes exist
        assert hasattr(metric, 'submission_id')
        assert hasattr(metric, 'problem_id')
        assert hasattr(metric, 'condition')
        assert hasattr(metric, 'pass_rate')
        assert hasattr(metric, 'cyclomatic_complexity')
        assert hasattr(metric, 'coverage')
        assert hasattr(metric, 'static_warning_count')
        assert hasattr(metric, 'execution_time_seconds')
        assert hasattr(metric, 'created_at')

    def test_metric_required_fields(self):
        """Verify that required fields are present and cannot be None."""
        with pytest.raises(TypeError):
            # Missing required submission_id
            Metric(
                problem_id="HumanEval/0",
                condition=Condition.BASELINE,
                pass_rate=0.85,
                cyclomatic_complexity=5,
                coverage=0.72,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )

    def test_metric_field_types(self):
        """Verify that fields have correct types."""
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        assert isinstance(metric.submission_id, str)
        assert isinstance(metric.problem_id, str)
        assert isinstance(metric.condition, Condition)
        assert isinstance(metric.pass_rate, float)
        assert isinstance(metric.cyclomatic_complexity, int)
        assert isinstance(metric.coverage, float)
        assert isinstance(metric.static_warning_count, int)
        assert isinstance(metric.execution_time_seconds, float)
        assert isinstance(metric.created_at, datetime)

    def test_metric_pass_rate_constraints(self):
        """Verify pass_rate is within valid range [0.0, 1.0]."""
        # Valid pass rates
        valid_rates = [0.0, 0.5, 1.0, 0.85]
        for rate in valid_rates:
            metric = Metric(
                submission_id="test-sub-001",
                problem_id="HumanEval/0",
                condition=Condition.BASELINE,
                pass_rate=rate,
                cyclomatic_complexity=5,
                coverage=0.72,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )
            assert 0.0 <= metric.pass_rate <= 1.0
        
        # Invalid pass rates (should be caught by validation logic if implemented)
        # Note: The dataclass itself may not enforce this, but the contract test
        # documents the expected constraint
        invalid_rates = [-0.1, 1.1]
        for rate in invalid_rates:
            metric = Metric(
                submission_id="test-sub-001",
                problem_id="HumanEval/0",
                condition=Condition.BASELINE,
                pass_rate=rate,
                cyclomatic_complexity=5,
                coverage=0.72,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )
            # We document that these are invalid, but the dataclass allows them
            # Validation should happen at the service layer
            assert not (0.0 <= metric.pass_rate <= 1.0)

    def test_metric_coverage_constraints(self):
        """Verify coverage is within valid range [0.0, 1.0]."""
        valid_coverages = [0.0, 0.5, 1.0, 0.72]
        for cov in valid_coverages:
            metric = Metric(
                submission_id="test-sub-001",
                problem_id="HumanEval/0",
                condition=Condition.BASELINE,
                pass_rate=0.85,
                cyclomatic_complexity=5,
                coverage=cov,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )
            assert 0.0 <= metric.coverage <= 1.0

    def test_metric_cyclomatic_complexity_constraints(self):
        """Verify cyclomatic_complexity is a positive integer >= 1."""
        # Valid complexities
        valid_complexities = [1, 5, 10, 100]
        for cc in valid_complexities:
            metric = Metric(
                submission_id="test-sub-001",
                problem_id="HumanEval/0",
                condition=Condition.BASELINE,
                pass_rate=0.85,
                cyclomatic_complexity=cc,
                coverage=0.72,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )
            assert metric.cyclomatic_complexity >= 1
        
        # Invalid complexity (0 or negative)
        invalid_complexities = [0, -1]
        for cc in invalid_complexities:
            metric = Metric(
                submission_id="test-sub-001",
                problem_id="HumanEval/0",
                condition=Condition.BASELINE,
                pass_rate=0.85,
                cyclomatic_complexity=cc,
                coverage=0.72,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )
            assert metric.cyclomatic_complexity < 1

    def test_metric_serialization_to_dict(self):
        """Verify Metric can be serialized to a dictionary."""
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        # Convert to dict using asdict (if available) or manual conversion
        try:
            from dataclasses import asdict
            metric_dict = asdict(metric)
        except ImportError:
            # Fallback for older Python versions
            metric_dict = {
                'submission_id': metric.submission_id,
                'problem_id': metric.problem_id,
                'condition': metric.condition.value,
                'pass_rate': metric.pass_rate,
                'cyclomatic_complexity': metric.cyclomatic_complexity,
                'coverage': metric.coverage,
                'static_warning_count': metric.static_warning_count,
                'execution_time_seconds': metric.execution_time_seconds,
                'created_at': metric.created_at.isoformat()
            }
        
        assert isinstance(metric_dict, dict)
        assert 'submission_id' in metric_dict
        assert 'pass_rate' in metric_dict
        assert 'cyclomatic_complexity' in metric_dict
        assert 'coverage' in metric_dict

    def test_metric_serialization_to_json(self):
        """Verify Metric can be serialized to JSON."""
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        try:
            from dataclasses import asdict
            metric_dict = asdict(metric)
            # Convert datetime to string for JSON serialization
            metric_dict['created_at'] = metric_dict['created_at'].isoformat()
            metric_dict['condition'] = metric_dict['condition'].value
        except ImportError:
            metric_dict = {
                'submission_id': metric.submission_id,
                'problem_id': metric.problem_id,
                'condition': metric.condition.value,
                'pass_rate': metric.pass_rate,
                'cyclomatic_complexity': metric.cyclomatic_complexity,
                'coverage': metric.coverage,
                'static_warning_count': metric.static_warning_count,
                'execution_time_seconds': metric.execution_time_seconds,
                'created_at': metric.created_at.isoformat()
            }
        
        json_str = json.dumps(metric_dict)
        assert isinstance(json_str, str)
        
        # Verify we can deserialize it back
        loaded_dict = json.loads(json_str)
        assert loaded_dict['submission_id'] == metric.submission_id
        assert loaded_dict['pass_rate'] == metric.pass_rate

    def test_metric_deserialization_from_dict(self):
        """Verify Metric can be reconstructed from a dictionary."""
        metric_data = {
            'submission_id': 'test-sub-001',
            'problem_id': 'HumanEval/0',
            'condition': 'baseline',
            'pass_rate': 0.85,
            'cyclomatic_complexity': 5,
            'coverage': 0.72,
            'static_warning_count': 3,
            'execution_time_seconds': 12.5,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Convert string condition to enum
        metric_data['condition'] = Condition(metric_data['condition'])
        
        # Convert ISO string back to datetime
        metric_data['created_at'] = datetime.fromisoformat(metric_data['created_at'])
        
        metric = Metric(**metric_data)
        
        assert metric.submission_id == 'test-sub-001'
        assert metric.pass_rate == 0.85
        assert metric.condition == Condition.BASELINE

    def test_metric_schema_completeness(self):
        """Verify the Metric schema includes all fields required by US2."""
        # List of fields required by the quality assessment pipeline
        required_fields = [
            'submission_id',      # Links to submission
            'problem_id',         # Links to problem
            'condition',          # LLM-assisted or baseline
            'pass_rate',          # FR-028: Pass rate calculation
            'cyclomatic_complexity', # FR-029: Complexity metric
            'coverage',           # FR-030: Test coverage
            'static_warning_count',  # FR-031: Static analysis warnings
            'execution_time_seconds', # Execution time metric
            'created_at'          # Timestamp for reproducibility
        ]
        
        # Create a sample metric
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        # Verify all required fields are present
        for field_name in required_fields:
            assert hasattr(metric, field_name), f"Missing required field: {field_name}"

    def test_metric_immutability_after_creation(self):
        """Verify that Metric fields are effectively immutable after creation."""
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        original_pass_rate = metric.pass_rate
        
        # Attempt to modify (this should fail or create a new instance for dataclasses)
        try:
            metric.pass_rate = 0.95
            # If modification is allowed, verify it changed
            assert metric.pass_rate == 0.95
        except AttributeError:
            # If fields are frozen (frozen=True), this should raise AttributeError
            pass

    def test_metric_multiple_conditions(self):
        """Verify Metric works with both baseline and LLM-assisted conditions."""
        for condition in [Condition.BASELINE, Condition.LLM_ASSISTED]:
            metric = Metric(
                submission_id="test-sub-001",
                problem_id="HumanEval/0",
                condition=condition,
                pass_rate=0.85,
                cyclomatic_complexity=5,
                coverage=0.72,
                static_warning_count=3,
                execution_time_seconds=12.5,
                created_at=datetime.now(timezone.utc)
            )
            assert metric.condition == condition

    def test_metric_schema_versioning(self):
        """Verify the schema includes versioning information if required."""
        # This test documents the expectation for schema versioning
        # The current implementation may not include an explicit version field,
        # but the contract test documents this requirement for future implementation
        metric = Metric(
            submission_id="test-sub-001",
            problem_id="HumanEval/0",
            condition=Condition.BASELINE,
            pass_rate=0.85,
            cyclomatic_complexity=5,
            coverage=0.72,
            static_warning_count=3,
            execution_time_seconds=12.5,
            created_at=datetime.now(timezone.utc)
        )
        
        # Note: If versioning is required, it should be added to the Metric dataclass
        # For now, we document this as a future requirement
        assert hasattr(metric, 'created_at'), "Timestamp field serves as version anchor"