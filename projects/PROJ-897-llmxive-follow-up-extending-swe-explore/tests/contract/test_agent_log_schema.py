"""
Contract test for agent_log_schema.yaml.

This test ensures that any generated agent logs strictly adhere to the
schema defined in contracts/agent_log_schema.yaml. It validates:
1. Top-level required fields (issue_id, agent_type, start_time, end_time, status).
2. Structure of the 'turns' list (query, retrieval, analysis, reformulation).
3. Data types for metrics (coverage_score, ranking_position).
4. Enum constraints for status and agent_type.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

# Add project root to path if running standalone
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.schemas import get_schema_path, load_schema

SCHEMA_FILE = "agent_log_schema.yaml"
SAMPLE_LOGS_DIR = Path("data/results/agent_logs")


def load_sample_logs() -> List[Dict[str, Any]]:
    """
    Loads sample agent logs from the data/results/agent_logs directory.
    If the directory is empty or missing, it returns an empty list.
    The test will be skipped if no samples exist yet (as this is a contract test
    for future generation).
    """
    sample_logs = []
    if not SAMPLE_LOGS_DIR.exists():
        # If the directory doesn't exist yet, we can't test against real data,
        # but the schema validation logic itself is what we are testing.
        return []

    for file_path in SAMPLE_LOGS_DIR.glob("*.jsonl"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    sample_logs.append(json.loads(line))
    return sample_logs


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Basic JSON Schema validation logic for the specific agent_log_schema.
    Since we are not using a heavy external validator library, we implement
    the specific checks defined in the schema manually to ensure compliance.
    """
    errors = []

    # 1. Check Required Top-Level Fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # 2. Validate Agent Type Enum
    agent_type = data.get("agent_type")
    if agent_type:
        allowed_types = schema.get("properties", {}).get("agent_type", {}).get("enum", [])
        if allowed_types and agent_type not in allowed_types:
            errors.append(f"Invalid agent_type '{agent_type}'. Must be one of {allowed_types}")

    # 3. Validate Status Enum
    status = data.get("status")
    if status:
        allowed_statuses = schema.get("properties", {}).get("status", {}).get("enum", [])
        if allowed_statuses and status not in allowed_statuses:
            errors.append(f"Invalid status '{status}'. Must be one of {allowed_statuses}")

    # 4. Validate Turns Structure
    turns = data.get("turns", [])
    if not isinstance(turns, list):
        errors.append("'turns' must be a list")
    else:
        turn_schema = schema.get("properties", {}).get("turns", {}).get("items", {})
        required_turn_fields = turn_schema.get("required", [])

        for i, turn in enumerate(turns):
            for field in required_turn_fields:
                if field not in turn:
                    errors.append(f"Turn {i} missing required field: {field}")

            # Check specific turn fields types if present
            if "query" in turn and not isinstance(turn["query"], str):
                errors.append(f"Turn {i}: 'query' must be a string")
            if "static_analysis_signals" in turn:
                signals = turn["static_analysis_signals"]
                if not isinstance(signals, list):
                    errors.append(f"Turn {i}: 'static_analysis_signals' must be a list")
                else:
                    for j, signal in enumerate(signals):
                        if not isinstance(signal, str):
                            errors.append(f"Turn {i}, Signal {j}: must be a string")

    # 5. Validate Metrics (if present)
    metrics = data.get("metrics", {})
    if metrics:
        if "coverage_score" in metrics and not isinstance(metrics["coverage_score"], (int, float)):
            errors.append("metrics.coverage_score must be a number")
        if "ranking_position" in metrics and not isinstance(metrics["ranking_position"], (int, float, type(None))):
            # ranking_position can be null for censored data
            errors.append("metrics.ranking_position must be a number or null")

    return errors


class TestAgentLogSchema:
    """
    Contract tests for the agent_log_schema.yaml.
    """

    @pytest.fixture(scope="class")
    def schema(self):
        """Load the agent log schema."""
        schema_path = get_schema_path(SCHEMA_FILE)
        assert schema_path.exists(), f"Schema file not found at {schema_path}"
        return load_schema(schema_path)

    def test_schema_exists_and_valid(self, schema):
        """Ensure the schema file is valid YAML and has the expected structure."""
        assert "type" in schema, "Schema must define a type"
        assert schema["type"] == "object", "Schema root type must be object"
        assert "properties" in schema, "Schema must define properties"
        assert "required" in schema, "Schema must define required fields"
        # Check for key expected fields
        expected_fields = ["issue_id", "agent_type", "turns", "status"]
        for field in expected_fields:
            assert field in schema["properties"], f"Schema missing expected field: {field}"

    def test_sample_logs_conform_to_schema(self, schema):
        """
        Validate that any existing sample logs in data/results/agent_logs
        strictly conform to the schema.
        """
        sample_logs = load_sample_logs()

        if not sample_logs:
            pytest.skip("No sample logs found in data/results/agent_logs to validate. "
                      "This test will pass by default until logs are generated.")

        all_errors = []
        for i, log in enumerate(sample_logs):
            errors = validate_against_schema(log, schema)
            if errors:
                all_errors.append(f"Log {i} (ID: {log.get('issue_id', 'unknown')}): {errors}")

        if all_errors:
            pytest.fail(f"Schema validation failed for {len(all_errors)} logs:\n" + "\n".join(all_errors))

    def test_required_fields_presence(self, schema):
        """
        Explicitly test that the schema enforces the critical fields
        required for the Wilcoxon signed-rank test pairing (issue_id).
        """
        required = schema.get("required", [])
        assert "issue_id" in required, "issue_id is critical for pairing and must be required"
        assert "agent_type" in required, "agent_type is critical for distinguishing baselines and must be required"
        assert "turns" in required, "turns are required to calculate metrics"

    def test_turn_structure_validity(self, schema):
        """
        Verify the schema defines the correct structure for a 'turn'.
        """
        turns_items = schema.get("properties", {}).get("turns", {}).get("items", {})
        required_turns = turns_items.get("required", [])

        # A turn must have a query and analysis signals
        assert "query" in required_turns, "Each turn must have a 'query'"
        assert "static_analysis_signals" in required_turns, "Each turn must have 'static_analysis_signals'"

        # Verify query is a string type in schema
        query_def = turns_items.get("properties", {}).get("query", {})
        assert query_def.get("type") == "string", "Query must be defined as a string"

        # Verify signals is an array
        signals_def = turns_items.get("properties", {}).get("static_analysis_signals", {})
        assert signals_def.get("type") == "array", "static_analysis_signals must be an array"