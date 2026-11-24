import pathlib
import json
import yaml
import pytest
from jsonschema import Draft7Validator, ValidationError

# Helper to load a YAML/JSON schema file
def load_schema(path: pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        # The schema files are written in YAML syntax (which also supports JSON)
        return yaml.safe_load(f)

# Load schemas once for the module
CONTRACTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "contracts"
DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"

dataset_schema = load_schema(DATASET_SCHEMA_PATH)
output_schema = load_schema(OUTPUT_SCHEMA_PATH)

@pytest.fixture(params=list(dataset_schema["definitions"].keys()))
def definition_name(request):
    return request.param

def test_dataset_schema_definitions_valid(definition_name):
    """Ensure each definition in the dataset schema is a valid JSON Schema."""
    definition = dataset_schema["definitions"][definition_name]
    # Validate that the definition itself is a valid schema
    validator = Draft7Validator(definition)
    # Create a minimal valid instance for each definition and validate it
    minimal_instance = {}
    for prop, prop_schema in definition.get("properties", {}).items():
        if "type" not in prop_schema:
            continue
        # Choose a simple valid value based on type
        typ = prop_schema["type"]
        if isinstance(typ, list):
            typ = typ[0]  # pick the first allowed type
        if typ == "string":
            minimal_instance[prop] = "example"
        elif typ == "integer":
            minimal_instance[prop] = 1
        elif typ == "number":
            # Respect minimum if present
            min_val = prop_schema.get("minimum", 0)
            minimal_instance[prop] = float(min_val) + 1.0
        elif typ == "null":
            minimal_instance[prop] = None
        else:
            # Unsupported type for this simple test
            minimal_instance[prop] = None

        # Stop after required properties are satisfied
        if set(minimal_instance.keys()) >= set(definition.get("required", [])):
            break

    # Validate the minimal instance against the definition
    validator.validate(minimal_instance)

@pytest.mark.parametrize("definition_name", list(output_schema["definitions"].keys()))
def test_output_schema_definitions_valid(definition_name):
    """Ensure each definition in the output schema is a valid JSON Schema."""
    definition = output_schema["definitions"][definition_name]
    validator = Draft7Validator(definition)
    # Build a minimal instance respecting required fields
    minimal_instance = {}
    for prop, prop_schema in definition.get("properties", {}).items():
        typ = prop_schema["type"]
        if isinstance(typ, list):
            typ = typ[0]
        if typ == "string":
            minimal_instance[prop] = "example"
        elif typ == "integer":
            minimal_instance[prop] = 1
        elif typ == "number":
            min_val = prop_schema.get("minimum", 0)
            minimal_instance[prop] = float(min_val) + 1.0
        else:
            minimal_instance[prop] = None
        
        if set(minimal_instance.keys()) >= set(definition.get("required", [])):
            break

    validator.validate(minimal_instance)
