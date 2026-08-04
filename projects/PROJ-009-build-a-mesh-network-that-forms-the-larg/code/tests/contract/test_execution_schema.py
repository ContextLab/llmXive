"""
Contract tests for ExecutionRun CSV schema.

These tests verify that ExecutionRun data conforms to the expected
schema defined in schemas.py, ensuring data integrity for downstream
analysis.
"""
import pytest
import json
from datetime import datetime
from orchestrator.models import ExecutionRun
from orchestrator.contract_validator import validate_schema, load_schema_from_yaml
from code.tests.contract.validator import SchemaValidationError
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA


def test_execution_run_schema_valid():
    """Test that a valid ExecutionRun passes schema validation."""
    valid_data = {
        "run_id": "test-run-001",
        "timestamp_start": "2024-01-15T08:00:00Z",
        "timestamp_end": "2024-01-15T08:30:00Z",
        "node_count": 15,
        "granularity": "medium",
        "injected_latency_ms": 25.0,
        "packet_loss_rate": 0.01,
        "throughput_ops_sec": 2500.75,
        "coordination_overhead_ratio": 0.12,
        "status": "completed"
    }
    
    errors = validate_schema(valid_data, EXECUTION_RUN_SCHEMA)
    assert len(errors) == 0, f"Unexpected validation errors: {errors}"


def test_execution_run_schema_missing_field():
    """Test that missing required fields are detected."""
    invalid_data = {
        "run_id": "test-run-002",
        "timestamp_start": "2024-01-15T08:00:00Z",
        # Missing timestamp_end
        "node_count": 10,
        "granularity": "fine",
        "injected_latency_ms": 10.0,
        "packet_loss_rate": 0.0,
        "throughput_ops_sec": 3000.0,
        "coordination_overhead_ratio": 0.05,
        "status": "completed"
    }
    
    errors = validate_schema(invalid_data, EXECUTION_RUN_SCHEMA)
    assert len(errors) > 0
    assert any("timestamp_end" in err for err in errors)


def test_execution_run_schema_invalid_type():
    """Test that incorrect types are rejected."""
    invalid_data = {
        "run_id": 12345,  # Should be string
        "timestamp_start": "2024-01-15T08:00:00Z",
        "timestamp_end": "2024-01-15T08:30:00Z",
        "node_count": "ten",  # Should be integer
        "granularity": "medium",
        "injected_latency_ms": 25.0,
        "packet_loss_rate": 0.01,
        "throughput_ops_sec": 2500.75,
        "coordination_overhead_ratio": 0.12,
        "status": "completed"
    }
    
    errors = validate_schema(invalid_data, EXECUTION_RUN_SCHEMA)
    assert len(errors) > 0
    assert any("run_id" in err for err in errors)
    assert any("node_count" in err for err in errors)


def test_execution_run_schema_invalid_enum():
    """Test that invalid enum values are rejected."""
    invalid_data = {
        "run_id": "test-run-003",
        "timestamp_start": "2024-01-15T08:00:00Z",
        "timestamp_end": "2024-01-15T08:30:00Z",
        "node_count": 10,
        "granularity": "super_fine",  # Invalid enum
        "injected_latency_ms": 25.0,
        "packet_loss_rate": 0.01,
        "throughput_ops_sec": 2500.75,
        "coordination_overhead_ratio": 0.12,
        "status": "completed"
    }
    
    errors = validate_schema(invalid_data, EXECUTION_RUN_SCHEMA)
    assert len(errors) > 0
    assert any("granularity" in err for err in errors)


def test_execution_run_schema_boundary_values():
    """Test boundary values for numeric fields."""
    # Test minimum values
    boundary_data = {
        "run_id": "test-run-004",
        "timestamp_start": "2024-01-15T08:00:00Z",
        "timestamp_end": "2024-01-15T08:30:00Z",
        "node_count": 1,  # Minimum valid
        "granularity": "coarse",
        "injected_latency_ms": 0.0,  # Minimum valid
        "packet_loss_rate": 0.0,  # Minimum valid
        "throughput_ops_sec": 0.0,  # Minimum valid
        "coordination_overhead_ratio": 0.0,  # Minimum valid
        "status": "completed"
    }
    
    errors = validate_schema(boundary_data, EXECUTION_RUN_SCHEMA)
    assert len(errors) == 0, f"Boundary values should be valid: {errors}"


def test_execution_run_schema_negative_values():
    """Test that negative values are rejected for non-negative fields."""
    invalid_data = {
        "run_id": "test-run-005",
        "timestamp_start": "2024-01-15T08:00:00Z",
        "timestamp_end": "2024-01-15T08:30:00Z",
        "node_count": -1,  # Invalid: negative
        "granularity": "medium",
        "injected_latency_ms": -10.0,  # Invalid: negative
        "packet_loss_rate": 0.01,
        "throughput_ops_sec": 2500.75,
        "coordination_overhead_ratio": 0.12,
        "status": "completed"
    }
    
    errors = validate_schema(invalid_data, EXECUTION_RUN_SCHEMA)
    assert len(errors) > 0
    assert any("node_count" in err for err in errors)
    assert any("injected_latency_ms" in err for err in errors)
