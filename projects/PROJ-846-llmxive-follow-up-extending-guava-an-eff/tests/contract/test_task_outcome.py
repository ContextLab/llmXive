"""
Contract test for TaskOutcome schema.

Verifies that evaluation results are recorded with the correct structure
and validates the schema constraints defined in data/models.py.
"""
import pytest
from datetime import datetime
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.models import TaskOutcome, FailureType, serialize_outcome
from utils.exceptions import ValidationThresholdError

def test_successful_outcome():
    """Test a successful task outcome."""
    outcome = TaskOutcome(
        trajectory_id="t1",
        success=True,
        steps=10,
        timestamp=datetime.now().isoformat(),
        failure_type=None,
        latency_induced=False
    )
    assert outcome.success is True
    assert outcome.failure_type is None
    assert outcome.latency_induced is False
    assert outcome.steps == 10

def test_failed_outcome():
    """Test a failed task outcome."""
    outcome = TaskOutcome(
        trajectory_id="t2",
        success=False,
        steps=5,
        timestamp=datetime.now().isoformat(),
        failure_type=FailureType.SEMANTIC,
        latency_induced=False
    )
    assert outcome.success is False
    assert outcome.failure_type == FailureType.SEMANTIC
    assert outcome.latency_induced is False

def test_latency_induced_failure():
    """Test a failure flagged as latency-induced."""
    outcome = TaskOutcome(
        trajectory_id="t3",
        success=False,
        steps=2,
        timestamp=datetime.now().isoformat(),
        failure_type=FailureType.LATENCY,
        latency_induced=True
    )
    assert outcome.latency_induced is True
    assert outcome.failure_type == FailureType.LATENCY

def test_schema_serialization():
    """Test that TaskOutcome can be serialized to JSON and back."""
    outcome = TaskOutcome(
        trajectory_id="t4",
        success=False,
        steps=15,
        timestamp=datetime.now().isoformat(),
        failure_type=FailureType.GEOMETRIC,
        latency_induced=False
    )
    
    serialized = serialize_outcome(outcome)
    assert isinstance(serialized, str)
    
    # Verify it's valid JSON
    parsed = json.loads(serialized)
    assert parsed["trajectory_id"] == "t4"
    assert parsed["success"] is False
    assert parsed["failure_type"] == "geometric"
    assert parsed["latency_induced"] is False

def test_validation_failure_type_mismatch():
    """Test that a non-None failure_type is required when success is False."""
    with pytest.raises(ValueError):
        TaskOutcome(
            trajectory_id="t5",
            success=False,
            steps=3,
            timestamp=datetime.now().isoformat(),
            failure_type=None,  # Invalid: failure_type must be set if success is False
            latency_induced=False
        )

def test_validation_latency_flag_consistency():
    """Test that latency_induced=True requires failure_type=FailureType.LATENCY."""
    # This should pass
    outcome = TaskOutcome(
        trajectory_id="t6",
        success=False,
        steps=1,
        timestamp=datetime.now().isoformat(),
        failure_type=FailureType.LATENCY,
        latency_induced=True
    )
    assert outcome.latency_induced is True

    # This should raise an error: latency_induced=True but failure_type is not LATENCY
    with pytest.raises(ValueError):
        TaskOutcome(
            trajectory_id="t7",
            success=False,
            steps=1,
            timestamp=datetime.now().isoformat(),
            failure_type=FailureType.SEMANTIC,
            latency_induced=True
        )

def test_validation_success_implies_no_failure_type():
    """Test that success=True implies failure_type=None."""
    # This should pass
    outcome = TaskOutcome(
        trajectory_id="t8",
        success=True,
        steps=20,
        timestamp=datetime.now().isoformat(),
        failure_type=None,
        latency_induced=False
    )
    assert outcome.success is True
    assert outcome.failure_type is None

    # This should raise an error: success=True but failure_type is set
    with pytest.raises(ValueError):
        TaskOutcome(
            trajectory_id="t9",
            success=True,
            steps=20,
            timestamp=datetime.now().isoformat(),
            failure_type=FailureType.SEMANTIC,
            latency_induced=False
        )

def test_enum_values():
    """Test that all expected FailureType enum values exist."""
    assert FailureType.SEMANTIC == "semantic"
    assert FailureType.GEOMETRIC == "geometric"
    assert FailureType.PERCEPTION == "perception"
    assert FailureType.LATENCY == "latency"
    assert FailureType.OTHER == "other"

def test_timestamp_format():
    """Test that timestamp is a valid ISO format string."""
    outcome = TaskOutcome(
        trajectory_id="t10",
        success=True,
        steps=5,
        timestamp=datetime.now().isoformat(),
        failure_type=None,
        latency_induced=False
    )
    # Should not raise
    datetime.fromisoformat(outcome.timestamp)