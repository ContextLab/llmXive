"""
Unit tests for the deterministic workflow generator.
Verifies that the generator produces the correct number of workflows,
respects the delegation depth constraints, ensures a minimum count per
depth level, and validates each workflow against the JSON schema.
"""

import pathlib
from collections import Counter

import yaml
import jsonschema

# Import the generator functions
from code.services.generator import generate_workflows


def load_schema() -> dict:
    """Load the workflow JSON schema from the contracts directory."""
    schema_path = (
        pathlib.Path(__file__)
        .resolve()
        .parents[2]  # navigate from tests/unit/ to project root
        / "contracts"
        / "workflow.schema.yaml"
    )
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_generate_workflows_count_and_depth():
    """Check that the generator creates the expected number of workflows
    with correct depth distribution and that each workflow validates
    against the schema."""
    count = 500
    seed = 42
    
    # Generate workflows
    workflows = generate_workflows(count, seed)
    
    # 1️⃣ Verify total count
    assert len(workflows) == count, f"Expected {count} workflows, got {len(workflows)}"
    
    # 2️⃣ Verify depth range and per-depth minimum
    depths = [wf["metadata"]["depth"] for wf in workflows]
    assert all(1 <= d <= 10 for d in depths), "All depths must be between 1 and 10"
    
    depth_counter = Counter(depths)
    for d in range(1, 11):
        assert depth_counter[d] >= 25, f"Depth {d} has fewer than 25 workflows"
    
    # 3️⃣ Validate each workflow against the JSON schema
    schema = load_schema()
    for wf in workflows:
        jsonschema.validate(instance=wf, schema=schema)