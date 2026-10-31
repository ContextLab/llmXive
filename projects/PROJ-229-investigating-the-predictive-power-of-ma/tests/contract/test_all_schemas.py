import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator, ValidationError

# Directory containing the contract schema files
CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

# Helper to load a YAML schema
def load_schema(name: str):
    schema_path = CONTRACTS_DIR / f"{name}.schema.yaml"
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Minimal valid instances for each schema
def example_dataset():
    return {
        "material_id": "mp-1234",
        "composition": "Fe2O3",
        "elemental_count": 2,
        "formation_energy": -1.23,
        "density": 5.2,
        "elemental_features": [1.0, 2.0, 3.0],
        "graph_features": [0.1, 0.2],
    }

def example_material_compound():
    return {
        "compound_id": "pcm-001",
        "formula": "Sb2Te3",
    }

def example_model_result():
    return {
        "model_type": "RandomForest",
        "trained_on": ["mp-1234", "mp-5678"],
        "validation_r2": 0.12,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def example_target_decision():
    return {
        "chosen_target": "latent_heat",
        "imputation_rate": 0.05,
        "proxy_correlation": 0.87,
        "fallback_flag": False,
    }

def example_validation_result():
    return {
        "validation_id": str(uuid.uuid4()),
        "dataset_source": "Literature PCMs",
        "rank_accuracy": 0.65,
        "false_positive_rate": 0.12,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@pytest.mark.parametrize(
    "schema_name, example_func",
    [
        ("dataset", example_dataset),
        ("material_compound", example_material_compound),
        ("model_result", example_model_result),
        ("target_decision", example_target_decision),
        ("validation_result", example_validation_result),
    ],
)
def test_schema_validation(schema_name: str, example_func):
    """
    Load each JSON‑schema and validate a minimal example instance.
    The test fails if the schema is malformed or the example does not
    conform to the specification.
    """
    schema = load_schema(schema_name)
    validator = Draft7Validator(schema)

    instance = example_func()
    # jsonschema raises ValidationError on first failure; we assert none occur
    try:
        validator.validate(instance)
    except ValidationError as exc:
        pytest.fail(f"Instance does not validate against {schema_name} schema: {exc.message}")

    # Additionally ensure that the schema itself is a valid Draft‑7 schema
    # (jsonschema will raise if the schema is malformed during validator creation)
    assert validator.is_valid(instance)  # sanity check that validation succeeded

def test_all_schemas_loadable():
    """
    Ensure that every schema file in the contracts directory can be parsed
    without raising an exception. This catches syntax errors or missing files.
    """
    for schema_file in CONTRACTS_DIR.glob("*.schema.yaml"):
        with schema_file.open("r", encoding="utf-8") as f:
            try:
                yaml.safe_load(f)
            except Exception as exc:
                pytest.fail(f"Failed to load schema {schema_file.name}: {exc}")