"""
JSON Schema definitions for validating llmXive project artifacts.
Derived from project contracts for dataset, agent_state, and result structures.
"""
from typing import Dict, Any, List, Optional
import json

# Dataset Schema (for generated training/test data)
DATASET_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "llmXive Dataset",
    "description": "Schema for generated propositional logic proofs and grid-world navigation tasks",
    "type": "object",
    "required": ["metadata", "instances"],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["version", "generation_seed", "task_type", "rule_set_id"],
            "properties": {
                "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                "generation_seed": {"type": "integer", "minimum": 0},
                "task_type": {"type": "string", "enum": ["logic_proofs", "grid_worlds", "mixed"]},
                "rule_set_id": {"type": "string"},
                "generated_at": {"type": "string", "format": "date-time"},
                "total_instances": {"type": "integer", "minimum": 1}
            }
        },
        "instances": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": ["instance_id", "type", "data"],
                        "properties": {
                            "instance_id": {"type": "string"},
                            "type": {"const": "logic_proof"},
                            "data": {
                                "type": "object",
                                "required": ["axioms", "goal", "proof_steps"],
                                "properties": {
                                    "axioms": {"type": "array", "items": {"type": "string"}},
                                    "goal": {"type": "string"},
                                    "proof_steps": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    },
                    {
                        "type": "object",
                        "required": ["instance_id", "type", "data"],
                        "properties": {
                            "instance_id": {"type": "string"},
                            "type": {"const": "grid_world"},
                            "data": {
                                "type": "object",
                                "required": ["grid_size", "start", "goal", "obstacles", "rules"],
                                "properties": {
                                    "grid_size": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                                    "start": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                                    "goal": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
                                    "obstacles": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}},
                                    "rules": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
}

# Agent State Schema (for tracking agent training progress)
AGENT_STATE_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "llmXive Agent State",
    "description": "Schema for agent state during training (rule-sets, evaluation counts, performance metrics)",
    "type": "object",
    "required": ["agent_id", "condition", "state_version", "rule_sets", "evaluation_stats"],
    "properties": {
        "agent_id": {"type": "string"},
        "condition": {"type": "string", "enum": ["sequential", "mixed", "coevolving"]},
        "state_version": {"type": "integer", "minimum": 0},
        "generation_step": {"type": "integer", "minimum": 0},
        "rule_sets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["rule_id", "rules", "fitness_score", "task_domains"],
                "properties": {
                    "rule_id": {"type": "string"},
                    "rules": {"type": "array", "items": {"type": "string"}},
                    "fitness_score": {"type": "number"},
                    "task_domains": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "evaluation_stats": {
            "type": "object",
            "required": ["total_evaluations", "evaluations_by_domain"],
            "properties": {
                "total_evaluations": {"type": "integer", "minimum": 0},
                "evaluations_by_domain": {
                    "type": "object",
                    "additionalProperties": {"type": "integer", "minimum": 0}
                }
            }
        },
        "performance_history": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step", "accuracy", "domains_tested"],
                "properties": {
                    "step": {"type": "integer"},
                    "accuracy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "domains_tested": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}

# Result Schema (for training run results and forgetting metrics)
RESULT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "llmXive Training Result",
    "description": "Schema for training run results including forgetting metrics and retention rates",
    "type": "object",
    "required": ["run_id", "condition", "seed", "final_state", "forgetting_metrics"],
    "properties": {
        "run_id": {"type": "string"},
        "condition": {"type": "string", "enum": ["sequential", "mixed", "coevolving"]},
        "seed": {"type": "integer", "minimum": 0},
        "config_snapshot": {"type": "object"},
        "final_state": {
            "type": "object",
            "required": ["agent_id", "condition", "state_version", "rule_sets", "evaluation_stats"],
            "properties": {
                "agent_id": {"type": "string"},
                "condition": {"type": "string"},
                "state_version": {"type": "integer"},
                "generation_step": {"type": "integer"},
                "rule_sets": {"type": "array"},
                "evaluation_stats": {"type": "object"}
            }
        },
        "forgetting_metrics": {
            "type": "object",
            "required": ["initial_accuracy", "final_accuracy", "accuracy_drop", "retention_rates"],
            "properties": {
                "initial_accuracy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "final_accuracy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "accuracy_drop": {"type": "number"},
                "retention_rates": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                }
            }
        },
        "evaluation_parity": {
            "type": "object",
            "required": ["expected_total", "actual_total", "parity_verified"],
            "properties": {
                "expected_total": {"type": "integer"},
                "actual_total": {"type": "integer"},
                "parity_verified": {"type": "boolean"}
            }
        },
        "generated_at": {"type": "string", "format": "date-time"}
    }
}

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any], schema_name: str) -> None:
    """
    Validate data against a JSON schema using basic Python validation.
    Raises ValueError if validation fails.
    
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        schema_name: Name of the schema for error messages
    """
    errors = _validate_object(data, schema, schema_name, "root")
    if errors:
        error_msg = f"Validation failed for {schema_name}:\n" + "\n".join(errors)
        raise ValueError(error_msg)

def _validate_object(data: Any, schema: Dict[str, Any], schema_name: str, path: str) -> List[str]:
    """Recursively validate data against schema, returning list of error messages."""
    errors = []
    
    schema_type = schema.get("type")
    
    if schema_type == "object":
        if not isinstance(data, dict):
            errors.append(f"{path}: Expected object, got {type(data).__name__}")
            return errors
        
        # Check required properties
        required = schema.get("required", [])
        for prop in required:
            if prop not in data:
                errors.append(f"{path}: Missing required property '{prop}'")
        
        # Validate properties
        properties = schema.get("properties", {})
        for prop, prop_schema in properties.items():
            if prop in data:
                errors.extend(_validate_object(
                    data[prop], 
                    prop_schema, 
                    schema_name, 
                    f"{path}.{prop}"
                ))
        
        # Check additionalProperties
        if "additionalProperties" not in schema:
            allowed_props = set(properties.keys())
            for key in data.keys():
                if key not in allowed_props:
                    errors.append(f"{path}: Unexpected property '{key}'")
                    
    elif schema_type == "array":
        if not isinstance(data, list):
            errors.append(f"{path}: Expected array, got {type(data).__name__}")
            return errors
        
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data):
                errors.extend(_validate_object(
                    item, 
                    items_schema, 
                    schema_name, 
                    f"{path}[{i}]"
                ))
                
    elif schema_type == "string":
        if not isinstance(data, str):
            errors.append(f"{path}: Expected string, got {type(data).__name__}")
        elif "pattern" in schema:
            import re
            if not re.match(schema["pattern"], data):
                errors.append(f"{path}: String '{data}' does not match pattern '{schema['pattern']}'")
        elif "enum" in schema:
            if data not in schema["enum"]:
                errors.append(f"{path}: String '{data}' not in allowed values {schema['enum']}")
                
    elif schema_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            errors.append(f"{path}: Expected integer, got {type(data).__name__}")
        else:
            if "minimum" in schema and data < schema["minimum"]:
                errors.append(f"{path}: Integer {data} is less than minimum {schema['minimum']}")
            if "maximum" in schema and data > schema["maximum"]:
                errors.append(f"{path}: Integer {data} is greater than maximum {schema['maximum']}")
                
    elif schema_type == "number":
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            errors.append(f"{path}: Expected number, got {type(data).__name__}")
        else:
            if "minimum" in schema and data < schema["minimum"]:
                errors.append(f"{path}: Number {data} is less than minimum {schema['minimum']}")
            if "maximum" in schema and data > schema["maximum"]:
                errors.append(f"{path}: Number {data} is greater than maximum {schema['maximum']}")
                
    elif schema_type == "boolean":
        if not isinstance(data, bool):
            errors.append(f"{path}: Expected boolean, got {type(data).__name__}")
            
    elif schema_type == "null":
        if data is not None:
            errors.append(f"{path}: Expected null, got {type(data).__name__}")
            
    return errors
