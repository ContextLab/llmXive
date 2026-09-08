"""
JSON Schema definitions and validators for dataset, agent_state, and result structures.
These schemas are derived from the project's contracts and used to validate data artifacts.
"""
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Schema Definitions
# ---------------------------------------------------------------------------

DATASET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Generated Dataset",
    "description": "Schema for generated training and test datasets (logic proofs and grid worlds).",
    "type": "object",
    "required": ["metadata", "data"],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["version", "seed", "generator", "timestamp"],
            "properties": {
                "version": {"type": "string"},
                "seed": {"type": "integer"},
                "generator": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "checksum": {"type": "string"}
            }
        },
        "data": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "title": "LogicProof",
                        "required": ["type", "id", "axioms", "conclusion", "proof_steps"],
                        "properties": {
                            "type": {"const": "logic_proof"},
                            "id": {"type": "string"},
                            "axioms": {"type": "array", "items": {"type": "string"}},
                            "conclusion": {"type": "string"},
                            "proof_steps": {"type": "array", "items": {"type": "object"}}
                        }
                    },
                    {
                        "type": "object",
                        "title": "GridWorld",
                        "required": ["type", "id", "grid_size", "start", "end", "obstacles", "rules"],
                        "properties": {
                            "type": {"const": "grid_world"},
                            "id": {"type": "string"},
                            "grid_size": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                            "start": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                            "end": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                            "obstacles": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}},
                            "rules": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                ]
            }
        }
    }
}

AGENT_STATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Agent State",
    "description": "Schema for the internal state of an agent during or after training.",
    "type": "object",
    "required": ["agent_type", "config", "population", "evaluation_stats"],
    "properties": {
        "agent_type": {"type": "string"},
        "config": {"type": "object"},
        "population": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "rules", "fitness"],
                "properties": {
                    "id": {"type": "string"},
                    "rules": {"type": "array", "items": {"type": "string"}},
                    "fitness": {"type": "number"}
                }
            }
        },
        "evaluation_stats": {
            "type": "object",
            "required": ["total_evaluations", "by_task"],
            "properties": {
                "total_evaluations": {"type": "integer"},
                "by_task": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"}
                }
            }
        },
        "generation_history": {
            "type": "array",
            "items": {"type": "object"}
        }
    }
}

RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Training Result",
    "description": "Schema for the final output of a training run (forgetting metrics, parity checks).",
    "type": "object",
    "required": ["run_id", "condition", "metrics", "parity_data"],
    "properties": {
        "run_id": {"type": "string"},
        "condition": {"type": "string", "enum": ["sequential", "mixed", "coevolving"]},
        "metrics": {
            "type": "object",
            "required": ["initial_accuracy", "final_accuracy", "forgetting_rate"],
            "properties": {
                "initial_accuracy": {"type": "number"},
                "final_accuracy": {"type": "number"},
                "forgetting_rate": {"type": "number"},
                "retention_rates": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                }
            }
        },
        "parity_data": {
            "type": "object",
            "required": ["total_evaluations", "checksum"],
            "properties": {
                "total_evaluations": {"type": "integer"},
                "checksum": {"type": "string"}
            }
        },
        "agent_state_snapshot": {"type": "object"}
    }
}

# ---------------------------------------------------------------------------
# Validator Class
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    """Represents a single validation error."""
    instance_path: str
    message: str
    schema_path: str = ""

@dataclass
class ValidationResult:
    """Result of a schema validation."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)

    def add_error(self, path: str, message: str, schema_path: str = ""):
        self.errors.append(ValidationError(path, message, schema_path))
        self.valid = False

class SchemaValidator:
    """
    Simple JSON Schema validator for the specific schemas defined above.
    Implements a subset of JSON Schema draft-07 sufficient for our contracts.
    """

    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def validate(self, instance: Any) -> ValidationResult:
        result = ValidationResult(valid=True)
        self._validate_node(instance, self.schema, "", result)
        return result

    def _validate_node(self, instance: Any, schema: Dict[str, Any], path: str, result: ValidationResult):
        # Type checking
        if "type" in schema:
            expected_type = schema["type"]
            if not self._check_type(instance, expected_type):
                result.add_error(path, f"Expected type '{expected_type}', got '{type(instance).__name__}'", "#/type")
                return # Stop further validation for this node if type is wrong

        # Enum checking
        if "enum" in schema:
            if instance not in schema["enum"]:
                result.add_error(path, f"Value '{instance}' not in enum {schema['enum']}", "#/enum")

        # Const checking
        if "const" in schema:
            if instance != schema["const"]:
                result.add_error(path, f"Value must be '{schema['const']}'", "#/const")

        # Object validation
        if schema.get("type") == "object" and isinstance(instance, dict):
            # Required properties
            if "required" in schema:
                for req in schema["required"]:
                    if req not in instance:
                        result.add_error(path, f"Missing required property '{req}'", "#/required")

            # Property validation
            if "properties" in schema:
                for key, value in instance.items():
                    if key in schema["properties"]:
                        self._validate_node(value, schema["properties"][key], f"{path}.{key}", result)
                    elif "additionalProperties" not in schema:
                        # Strict mode: reject unknown properties if not explicitly allowed
                        # For this project, we are strict on top-level known fields
                        pass # Allow additional properties for now unless specified

        # Array validation
        if schema.get("type") == "array" and isinstance(instance, list):
            if "items" in schema:
                for i, item in enumerate(instance):
                    self._validate_node(item, schema["items"], f"{path}[{i}]", result)

        # String format (basic check)
        if schema.get("type") == "string" and schema.get("format") == "date-time":
            # Basic ISO 8601 check
            import re
            if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", str(instance)):
                result.add_error(path, "Invalid date-time format", "#/format")

    def _check_type(self, instance: Any, expected: str) -> bool:
        if expected == "string":
            return isinstance(instance, str)
        elif expected == "integer":
            return isinstance(instance, int) and not isinstance(instance, bool)
        elif expected == "number":
            return isinstance(instance, (int, float)) and not isinstance(instance, bool)
        elif expected == "boolean":
            return isinstance(instance, bool)
        elif expected == "array":
            return isinstance(instance, list)
        elif expected == "object":
            return isinstance(instance, dict)
        elif expected == "null":
            return instance is None
        return False

# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def validate_dataset(data: Dict[str, Any]) -> ValidationResult:
    """Validates a dataset structure against the DATASET_SCHEMA."""
    validator = SchemaValidator(DATASET_SCHEMA)
    return validator.validate(data)

def validate_agent_state(state: Dict[str, Any]) -> ValidationResult:
    """Validates an agent state structure against the AGENT_STATE_SCHEMA."""
    validator = SchemaValidator(AGENT_STATE_SCHEMA)
    return validator.validate(state)

def validate_result(result: Dict[str, Any]) -> ValidationResult:
    """Validates a training result structure against the RESULT_SCHEMA."""
    validator = SchemaValidator(RESULT_SCHEMA)
    return validator.validate(result)
