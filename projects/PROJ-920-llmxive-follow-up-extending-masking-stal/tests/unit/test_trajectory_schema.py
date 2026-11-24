"""
Unit test that validates each generated trajectory against the JSON schema
defined in `contracts/trajectory.schema.yaml`.
"""

import json
import pathlib
import pytest
import yaml
from jsonschema import Draft7Validator, ValidationError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TRAJECTORY_JSON_PATH = PROJECT_ROOT / "data" / "raw" / "trajectories.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "trajectory.schema.yaml"

@pytest.fixture(scope="module")
def trajectories():
    if not TRAJECTORY_JSON_PATH.exists():
        pytest.fail(f"Trajectory file missing at {TRAJECTORY_JSON_PATH}")
    with open(TRAJECTORY_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@pytest.fixture(scope="module")
def schema():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file missing at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_trajectories_conform_to_schema(trajectories, schema):
    validator = Draft7Validator(schema)
    errors = []
    for idx, traj in enumerate(trajectories):
        try:
            validator.validate(traj)
        except ValidationError as e:
            errors.append(f"Trajectory {idx} failed: {e.message}")

    if errors:
        pytest.fail(f"{len(errors)} trajectories failed schema validation. First: {errors[0]}")