"""
Contract test verifying output JSON structure matches contracts/output_schema.yaml.

This test ensures that the static scoring output adheres to the defined schema:
- ReasoningTrace: task_id (str), tokens (list), static_scores (list), dynamic_scores (list)
- BranchingScore: task_id (str), position (int), score (float), type (str: static/dynamic)
- CorrelationResult: pearson (float), spearman (float), p_value (float), seeds (list), inconclusive_flag (bool)

The test loads the generated static_scores.json (if it exists) and validates
the structure against the schema defined in contracts/output_schema.yaml.
"""
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

SCHEMA_PATH = project_root / "contracts" / "output_schema.yaml"
OUTPUT_PATH = project_root / "data" / "processed" / "static_scores.json"

@pytest.fixture
def schema() -> Dict[str, Any]:
    """Load the output schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture
def output_data() -> Optional[Dict[str, Any]]:
    """Load the generated static scores output if it exists."""
    if not OUTPUT_PATH.exists():
        pytest.skip(f"Output file not found: {OUTPUT_PATH}. Run T017 first.")
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_reasoning_trace(trace: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a ReasoningTrace against the schema."""
    required_fields = schema.get("ReasoningTrace", {}).get("required", [])
    field_types = schema.get("ReasoningTrace", {}).get("properties", {})

    for field in required_fields:
        assert field in trace, f"Missing required field: {field}"

    for field, value in trace.items():
        expected_type = field_types.get(field, {}).get("type")
        if expected_type == "string":
            assert isinstance(value, str), f"Field '{field}' must be str, got {type(value)}"
        elif expected_type == "array":
            assert isinstance(value, list), f"Field '{field}' must be list, got {type(value)}"
        elif expected_type == "number":
            # Allow int or float
            assert isinstance(value, (int, float)), f"Field '{field}' must be number, got {type(value)}"

def validate_branching_score(score: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a BranchingScore against the schema."""
    required_fields = schema.get("BranchingScore", {}).get("required", [])
    field_types = schema.get("BranchingScore", {}).get("properties", {})

    for field in required_fields:
        assert field in score, f"Missing required field: {field}"

    for field, value in score.items():
        expected_type = field_types.get(field, {}).get("type")
        if expected_type == "string":
            assert isinstance(value, str), f"Field '{field}' must be str, got {type(value)}"
        elif expected_type == "integer":
            assert isinstance(value, int), f"Field '{field}' must be int, got {type(value)}"
        elif expected_type == "number":
            assert isinstance(value, (int, float)), f"Field '{field}' must be number, got {type(value)}"
        elif expected_type == "array":
            assert isinstance(value, list), f"Field '{field}' must be list, got {type(value)}"

    # Validate 'type' field is either 'static' or 'dynamic'
    if "type" in score:
        assert score["type"] in ["static", "dynamic"], f"Invalid branching score type: {score['type']}"

def validate_correlation_result(result: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a CorrelationResult against the schema."""
    required_fields = schema.get("CorrelationResult", {}).get("required", [])
    field_types = schema.get("CorrelationResult", {}).get("properties", {})

    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    for field, value in result.items():
        expected_type = field_types.get(field, {}).get("type")
        if expected_type == "string":
            assert isinstance(value, str), f"Field '{field}' must be str, got {type(value)}"
        elif expected_type == "number":
            assert isinstance(value, (int, float)), f"Field '{field}' must be number, got {type(value)}"
        elif expected_type == "array":
            assert isinstance(value, list), f"Field '{field}' must be list, got {type(value)}"
        elif expected_type == "boolean":
            assert isinstance(value, bool), f"Field '{field}' must be bool, got {type(value)}"

@pytest.mark.contract
def test_static_output_structure_matches_schema(schema: Dict[str, Any], output_data: Dict[str, Any]) -> None:
    """
    Contract test: Verify that the static_scores.json output structure matches the schema.
    
    The output file is expected to be a list of ReasoningTrace objects.
    Each ReasoningTrace may contain a list of BranchingScores.
    """
    assert isinstance(output_data, list), "Output data must be a list of traces"
    
    assert len(output_data) > 0, "Output data must not be empty"

    for i, trace in enumerate(output_data):
        assert isinstance(trace, dict), f"Trace {i} must be a dictionary"
        
        # Validate ReasoningTrace structure
        validate_reasoning_trace(trace, schema)

        # If static_scores are present, validate them as BranchingScores
        if "static_scores" in trace and trace["static_scores"]:
            assert isinstance(trace["static_scores"], list), "static_scores must be a list"
            for j, score in enumerate(trace["static_scores"]):
                validate_branching_score(score, schema)

        # If dynamic_scores are present (optional in static output), validate them
        if "dynamic_scores" in trace and trace["dynamic_scores"]:
            assert isinstance(trace["dynamic_scores"], list), "dynamic_scores must be a list"
            for j, score in enumerate(trace["dynamic_scores"]):
                validate_branching_score(score, schema)

@pytest.mark.contract
def test_schema_definitions_exist(schema: Dict[str, Any]) -> None:
    """
    Contract test: Verify that all required schema definitions exist.
    """
    required_definitions = ["ReasoningTrace", "BranchingScore", "CorrelationResult"]
    for definition in required_definitions:
        assert definition in schema, f"Schema definition '{definition}' is missing"
        
        # Check for required fields
        assert "required" in schema[definition], f"Schema '{definition}' missing 'required' field"
        assert "properties" in schema[definition], f"Schema '{definition}' missing 'properties' field"