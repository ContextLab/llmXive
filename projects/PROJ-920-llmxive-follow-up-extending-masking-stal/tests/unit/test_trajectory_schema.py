"""
Unit test that validates each generated trajectory against the JSON schema
defined in ``contracts/trajectory.schema.yaml``.
"""

import json
import pathlib

import pytest
import yaml
from jsonschema import Draft7Validator, ValidationError

# Resolve project-root relative paths
# projects/PROJ-920-llmxive-follow-up-extending-masking-stal/tests/unit/test_trajectory_schema.py
# parents[0]: tests/unit, parents[1]: tests, parents[2]: project_root
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

TRAJECTORY_JSON_PATH = PROJECT_ROOT / "data" / "raw" / "trajectories.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "trajectory.schema.yaml"


@pytest.fixture(scope="module")
def trajectories():
    """Load the list of trajectories from the JSON file."""
    if not TRAJECTORY_JSON_PATH.exists():
        pytest.fail(f"Trajectory file missing at {TRAJECTORY_JSON_PATH}")
    with open(TRAJECTORY_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Trajectories JSON must be a list"
    return data


@pytest.fixture(scope="module")
def schema():
    """Load the JSON schema (YAML format) for a trajectory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file missing at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        raw_schema = yaml.safe_load(f)
    assert isinstance(raw_schema, dict), "Schema file must contain a JSON schema dict"
    return raw_schema


def test_trajectories_conform_to_schema(trajectories, schema):
    """Validate every trajectory against the contract schema."""
    validator = Draft7Validator(schema)

    errors = []
    for idx, traj in enumerate(trajectories):
        try:
            validator.validate(traj)
        except ValidationError as e:
            errors.append(f"Trajectory {idx} failed validation: {e.message}")

    if errors:
        summary = "\n".join(errors[:5])
        pytest.fail(
            f"{len(errors)} trajectory(s) did not conform to the schema. "
            f"First failures:\n{summary}"
        )