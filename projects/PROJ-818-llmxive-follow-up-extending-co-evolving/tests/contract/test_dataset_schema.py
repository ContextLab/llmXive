"""
Contract tests for dataset schema validation.
Validates the structure of generated datasets (logic proofs and grid worlds).
"""
import json
import os
import pytest
from typing import Any, Dict, List

# Define the expected schema structure for datasets
DATASET_SCHEMA = {
    "required_keys": ["metadata", "instances"],
    "metadata_keys": ["seed", "task_type", "rule_set_id", "generation_count", "checksum"],
    "instance_keys": ["id", "problem", "solution", "rules_applied"],
    "task_types": ["logic_proof", "grid_navigation"],
    "problem_types": {
        "logic_proof": {
            "required": ["axioms", "goal"],
            "optional": ["intermediate_steps"]
        },
        "grid_navigation": {
            "required": ["grid_size", "start", "end", "obstacles", "rules"],
            "optional": ["path"]
        }
    }
}

def validate_dataset_structure(data: Dict[str, Any]) -> List[str]:
    """
    Validates a dataset dictionary against the expected schema.
    Returns a list of validation errors (empty if valid).
    """
    errors = []

    # Check top-level required keys
    for key in DATASET_SCHEMA["required_keys"]:
        if key not in data:
            errors.append(f"Missing required top-level key: {key}")

    if "metadata" in data:
        meta = data["metadata"]
        for key in DATASET_SCHEMA["metadata_keys"]:
            if key not in meta:
                errors.append(f"Missing required metadata key: {key}")

        # Validate task_type
        if "task_type" in meta and meta["task_type"] not in DATASET_SCHEMA["task_types"]:
            errors.append(f"Invalid task_type: {meta['task_type']}")

    if "instances" in data:
        if not isinstance(data["instances"], list):
            errors.append("'instances' must be a list")
        else:
            for i, instance in enumerate(data["instances"]):
                prefix = f"Instance {i}"
                for key in DATASET_SCHEMA["instance_keys"]:
                    if key not in instance:
                        errors.append(f"{prefix}: Missing required key '{key}'")

                # Validate problem structure based on task type
                if "metadata" in data and "task_type" in data["metadata"]:
                    task_type = data["metadata"]["task_type"]
                    if task_type in DATASET_SCHEMA["problem_types"]:
                        problem_schema = DATASET_SCHEMA["problem_types"][task_type]
                        problem = instance.get("problem", {})
                        for req_key in problem_schema.get("required", []):
                            if req_key not in problem:
                                errors.append(f"{prefix}: Problem missing required key '{req_key}'")

    return errors

def load_dataset(filepath: str) -> Dict[str, Any]:
    """Load a dataset from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

@pytest.mark.contract
def test_logic_dataset_schema():
    """Test that a generated logic proof dataset conforms to the schema."""
    # This test will fail if the file doesn't exist yet, which is expected
    # before T011/T014 are run. The task is to implement the validator.
    try:
        dataset = load_dataset("data/proofs_dataset.json")
        errors = validate_dataset_structure(dataset)
        assert len(errors) == 0, f"Schema validation failed: {errors}"
    except FileNotFoundError:
        pytest.skip("Dataset file not found. Run generation tasks first.")

@pytest.mark.contract
def test_grid_dataset_schema():
    """Test that a generated grid navigation dataset conforms to the schema."""
    try:
        dataset = load_dataset("data/grids_dataset.json")
        errors = validate_dataset_structure(dataset)
        assert len(errors) == 0, f"Schema validation failed: {errors}"
    except FileNotFoundError:
        pytest.skip("Dataset file not found. Run generation tasks first.")