"""
Contract test for ExecutionRun CSV schema.
Implements T011.

Validates that data produced by the orchestrator (specifically from data_collector.py
and scheduler.py) conforms to the ExecutionRun schema defined in the contract validator.
"""
import pytest
import json
from datetime import datetime
from orchestrator.models import ExecutionRun
from orchestrator.contract_validator import validate_schema, load_schema_from_yaml
from code.tests.contract.validator import SchemaValidationError

# Define the expected schema structure for ExecutionRun based on data-model.md and models.py
EXECUTION_RUN_SCHEMA = {
    "type": "object",
    "required": [
        "id",
        "timestamp",
        "node_count",
        "granularity",
        "throughput_ops",
        "latency_ms",
        "injected_latency_ms",
        "packet_loss_rate",
        "cpu_utilization_pct",
        "status"
    ],
    "properties": {
        "id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "node_count": {"type": "integer", "minimum": 1},
        "granularity": {"type": "string", "enum": ["fine", "medium", "coarse"]},
        "throughput_ops": {"type": "number"},
        "latency_ms": {"type": "number"},
        "injected_latency_ms": {"type": "number"},
        "packet_loss_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "cpu_utilization_pct": {"type": "number", "minimum": 0.0, "maximum": 100.0},
        "status": {"type": "string", "enum": ["running", "completed", "failed", "timeout"]}
    }
}

def test_execution_run_schema_valid():
    """Test that a valid ExecutionRun dictionary passes schema validation."""
    data = {
        "id": "run-001",
        "timestamp": datetime.now().isoformat(),
        "node_count": 10,
        "granularity": "medium",
        "throughput_ops": 1200.5,
        "latency_ms": 45.2,
        "injected_latency_ms": 10.0,
        "packet_loss_rate": 0.01,
        "cpu_utilization_pct": 75.5,
        "status": "completed"
    }
    
    # Validate using the contract validator which uses pyyaml/jsonschema logic
    result = validate_schema(data, "ExecutionRun")
    assert result is True

def test_execution_run_schema_missing_field():
    """Test that a missing required field raises SchemaValidationError."""
    data = {
        "id": "run-001",
        "timestamp": datetime.now().isoformat(),
        "node_count": 10,
        "granularity": "medium",
        "throughput_ops": 1200.5,
        # Missing latency_ms, injected_latency_ms, packet_loss_rate, cpu_utilization_pct, status
    }
    
    with pytest.raises(SchemaValidationError, match="Missing required field"):
        validate_schema(data, "ExecutionRun")

def test_execution_run_schema_invalid_type():
    """Test that an invalid type for a field raises SchemaValidationError."""
    data = {
        "id": "run-001",
        "timestamp": datetime.now().isoformat(),
        "node_count": "ten",  # Should be integer
        "granularity": "medium",
        "throughput_ops": 1200.5,
        "latency_ms": 45.2,
        "injected_latency_ms": 10.0,
        "packet_loss_rate": 0.01,
        "cpu_utilization_pct": 75.5,
        "status": "completed"
    }
    
    with pytest.raises(SchemaValidationError, match="Invalid type"):
        validate_schema(data, "ExecutionRun")

def test_execution_run_schema_invalid_enum():
    """Test that an invalid enum value raises SchemaValidationError."""
    data = {
        "id": "run-001",
        "timestamp": datetime.now().isoformat(),
        "node_count": 10,
        "granularity": "ultra-fine",  # Not in enum [fine, medium, coarse]
        "throughput_ops": 1200.5,
        "latency_ms": 45.2,
        "injected_latency_ms": 10.0,
        "packet_loss_rate": 0.01,
        "cpu_utilization_pct": 75.5,
        "status": "completed"
    }
    
    with pytest.raises(SchemaValidationError, match="Invalid value for field 'granularity'"):
        validate_schema(data, "ExecutionRun")

def test_execution_run_schema_boundary_values():
    """Test boundary values for numeric fields."""
    data = {
        "id": "run-002",
        "timestamp": datetime.now().isoformat(),
        "node_count": 1,  # Minimum
        "granularity": "fine",
        "throughput_ops": 0.0,  # Minimum valid
        "latency_ms": 0.0,
        "injected_latency_ms": 0.0,
        "packet_loss_rate": 0.0,  # Minimum
        "cpu_utilization_pct": 0.0,
        "status": "running"
    }
    
    assert validate_schema(data, "ExecutionRun") is True

    data_max = data.copy()
    data_max["node_count"] = 1000
    data_max["packet_loss_rate"] = 1.0  # Maximum
    data_max["cpu_utilization_pct"] = 100.0  # Maximum
    
    assert validate_schema(data_max, "ExecutionRun") is True

def test_execution_run_schema_negative_values():
    """Test that negative values for non-negative fields raise errors."""
    data = {
        "id": "run-003",
        "timestamp": datetime.now().isoformat(),
        "node_count": 10,
        "granularity": "medium",
        "throughput_ops": -5.0,  # Invalid negative
        "latency_ms": 45.2,
        "injected_latency_ms": 10.0,
        "packet_loss_rate": 0.01,
        "cpu_utilization_pct": 75.5,
        "status": "completed"
    }
    
    with pytest.raises(SchemaValidationError, match="Invalid value"):
        validate_schema(data, "ExecutionRun")