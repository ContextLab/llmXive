import pytest
import json
import yaml
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def load_schema(schema_path: str) -> dict:
    """Load a JSON schema from a YAML file."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_execution_log(log: dict, schema: dict) -> bool:
    """Basic validation of execution log against schema."""
    # Check required fields
    for field in schema.get("required", []):
        if field not in log:
            return False

    # Check context_reduction_pct type
    if "context_reduction_pct" in log:
        val = log["context_reduction_pct"]
        if not isinstance(val, (int, float, str)):
            return False
        if isinstance(val, str) and val != "[deferred]":
            return False

    # Check violation_details structure
    if "violation_details" in log:
        for detail in log["violation_details"]:
            if "node_id" not in detail or "rule_id" not in detail:
                return False

    return True


def test_execution_log_schema():
    """Test that generated execution logs conform to the schema."""
    schema = load_schema("contracts/execution_log.schema.yaml")

    # Generate test logs
    from generators.synthetic_workflow import SyntheticWorkflowGenerator
    from engines.full_context import FullContextEngine
    from engines.compressed_context import CompressedContextEngine

    generator = SyntheticWorkflowGenerator(seed=42)
    workflows = generator.generate_workflows(10)

    full_engine = FullContextEngine()
    compressed_engine = CompressedContextEngine(traversal_depth=2)

    for workflow in workflows:
        full_log = full_engine.execute(workflow)
        compressed_log = compressed_engine.execute(workflow)

        assert validate_execution_log(full_log, schema), "Full log does not conform"
        assert validate_execution_log(compressed_log, schema), "Compressed log does not conform"

    print("All execution log schema tests passed.")


if __name__ == "__main__":
    test_execution_log_schema()
