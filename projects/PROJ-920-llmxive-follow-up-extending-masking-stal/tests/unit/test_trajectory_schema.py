"""
Unit test that validates each generated trajectory against the JSON schema
defined in ``contracts/trajectory.schema.yaml``.
"""

import json
import pathlib

import pytest
import yaml
from jsonschema import Draft7Validator, ValidationError

# Resolve project‑root relative paths
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]

TRAJECTORY_JSON_PATH = PROJECT_ROOT / "data" / "raw" / "trajectories.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "trajectory.schema.yaml"


@pytest.fixture(scope="module")
def trajectories():
    """Load the list of trajectories from the JSON file."""
    with open(TRAJECTORY_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Trajectories JSON must be a list"
    return data


@pytest.fixture(scope="module")
def schema():
    """Load the JSON schema (YAML format) for a trajectory."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        raw_schema = yaml.safe_load(f)
    # jsonschema expects a dict; ensure top‑level schema is a dict
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
        # Provide a concise summary of the first few failures to aid debugging
        summary = "\n".join(errors[:5])
        pytest.fail(
            f"{len(errors)} trajectory(s) did not conform to the schema. "
            f"First failures:\n{summary}"
        )