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


def validate_workflow(workflow: dict, schema: dict) -> bool:
    """Basic validation of workflow against schema."""
    # Check required fields
    for field in schema.get("required", []):
        if field not in workflow:
            return False

    # Check nodes structure
    if "nodes" in workflow:
        for node in workflow["nodes"]:
            for req in schema["properties"]["nodes"]["items"].get("required", []):
                if req not in node:
                    return False

    return True


def test_workflow_schema():
    """Test that generated workflows conform to the schema."""
    schema = load_schema("contracts/workflow.schema.yaml")

    # Generate a test workflow
    from generators.synthetic_workflow import SyntheticWorkflowGenerator
    generator = SyntheticWorkflowGenerator(seed=42)
    workflows = generator.generate_workflows(10)

    for w in workflows:
        assert validate_workflow(w, schema), f"Workflow {w['id']} does not conform to schema"

    print("All workflow schema tests passed.")


if __name__ == "__main__":
    test_workflow_schema()
