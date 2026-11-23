"""
Contract test for ExecutionOutcome schema validation.
Validates the ExecutionOutcome dataclass against the JSON Schema defined in
specs/001-symbolic-dojo-extend/contracts/execution_outcome.schema.yaml.
"""
import pytest
import sys
from pathlib import Path
import json
import yaml

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.executor import ExecutionOutcome


class TestExecutionOutcomeContract:
    """Tests for ExecutionOutcome schema compliance."""

    @pytest.fixture
    def schema(self):
        """Load the ExecutionOutcome schema from the specs directory."""
        schema_path = Path(__file__).parent.parent.parent.parent / "specs" / "001-symbolic-dojo-extend" / "contracts" / "execution_outcome.schema.yaml"
        if not schema_path.exists():
            pytest.fail(f"Schema file not found at {schema_path}")
        
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)

    def test_valid_success_outcome(self, schema):
        """Test a successful execution outcome against the schema."""
        outcome = ExecutionOutcome(
            task_id="task_001",
            success=True,
            failure_mode=None,
            timestamp="2023-10-27T10:00:00Z"
        )
        
        # Convert to dict for validation
        data = outcome.__dict__
        
        # Validate against JSON schema
        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Validation failed: {e.message}")

    def test_valid_failure_outcome(self, schema):
        """Test a failed execution outcome against the schema."""
        outcome = ExecutionOutcome(
            task_id="task_002",
            success=False,
            failure_mode="Controller Execution Failure",
            timestamp="2023-10-27T10:05:00Z"
        )
        
        data = outcome.__dict__
        
        from jsonschema import validate, ValidationError
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Validation failed: {e.message}")

    def test_invalid_failure_mode(self, schema):
        """Test that an invalid failure_mode raises a validation error."""
        outcome = ExecutionOutcome(
            task_id="task_003",
            success=False,
            failure_mode="Invalid Failure Mode",
            timestamp="2023-10-27T10:10:00Z"
        )
        
        data = outcome.__dict__
        
        from jsonschema import validate, ValidationError
        with pytest.raises(ValidationError):
            validate(instance=data, schema=schema)

    def test_missing_required_field(self, schema):
        """Test that a missing required field raises a validation error."""
        # Create a dict missing 'task_id'
        invalid_data = {
            "success": True,
            "failure_mode": None,
            "timestamp": "2023-10-27T10:15:00Z"
        }
        
        from jsonschema import validate, ValidationError
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_serialization_roundtrip(self, schema):
        """Test that ExecutionOutcome can be serialized and validated."""
        outcome = ExecutionOutcome(
            task_id="task_004",
            success=False,
            failure_mode="Planner Infeasibility",
            timestamp="2023-10-27T10:20:00Z"
        )
        
        # Serialize to JSON string
        json_str = json.dumps(outcome.__dict__)
        data = json.loads(json_str)
        
        # Validate the deserialized data
        from jsonschema import validate, ValidationError
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Roundtrip validation failed: {e.message}")