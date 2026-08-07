"""
Contract tests specifically for ExecutionRun schema.

These tests verify that the ExecutionRun structure conforms to the
defined schema and handles edge cases correctly.
"""

import pytest
import json
from datetime import datetime
from orchestrator.models import ExecutionRun
from orchestrator.contract_validator import validate_schema, load_schema_from_yaml
from code.tests.contract.validator import SchemaValidationError
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA


def test_execution_run_schema_valid():
    """Test that a valid ExecutionRun passes validation."""
    valid_run = {
        "node_count": 10,
        "granularity": "coarse",
        "throughput": 2500.75,
        "overhead_ratio": 0.08,
        "run_id": "run-20231027-001",
        "timestamp": datetime.now().isoformat()
    }
    
    # Validate against schema
    validate_schema(valid_run, EXECUTION_RUN_SCHEMA)
    # Should not raise
    assert True
    
    
def test_execution_run_schema_missing_field():
    """Test that missing required fields are caught."""
    incomplete_run = {
        "node_count": 10,
        "granularity": "coarse"
        # Missing throughput and overhead_ratio
    }
    
    with pytest.raises(SchemaValidationError):
        validate_schema(incomplete_run, EXECUTION_RUN_SCHEMA)
        
    
def test_execution_run_schema_invalid_type():
    """Test that invalid types are caught."""
    invalid_run = {
        "node_count": "ten",  # Should be int
        "granularity": "coarse",
        "throughput": 2500.75,
        "overhead_ratio": 0.08
    }
    
    with pytest.raises(SchemaValidationError):
        validate_schema(invalid_run, EXECUTION_RUN_SCHEMA)
        
    
def test_execution_run_schema_invalid_enum():
    """Test that invalid enum values are caught."""
    invalid_run = {
        "node_count": 10,
        "granularity": "ultra-fine",  # Not in enum
        "throughput": 2500.75,
        "overhead_ratio": 0.08
    }
    
    with pytest.raises(SchemaValidationError):
        validate_schema(invalid_run, EXECUTION_RUN_SCHEMA)
        
    
def test_execution_run_schema_boundary_values():
    """Test boundary values for numeric fields."""
    boundary_run = {
        "node_count": 1,
        "granularity": "fine",
        "throughput": 0.0,
        "overhead_ratio": 0.0
    }
    
    # Should pass
    validate_schema(boundary_run, EXECUTION_RUN_SCHEMA)
    
    
def test_execution_run_schema_negative_values():
    """Test that negative values are rejected where minimum is 0."""
    invalid_run = {
        "node_count": 10,
        "granularity": "coarse",
        "throughput": -100.0,  # Negative throughput
        "overhead_ratio": 0.08
    }
    
    with pytest.raises(SchemaValidationError):
        validate_schema(invalid_run, EXECUTION_RUN_SCHEMA)
