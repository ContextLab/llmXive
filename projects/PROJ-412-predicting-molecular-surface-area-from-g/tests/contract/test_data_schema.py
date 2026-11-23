"""Contract test validating the dataset schema defines the required fields."""
import yaml
from pathlib import Path

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs" / "001-predicting-molecular-surface-area-from-g"
    / "contracts" / "dataset.schema.yaml"
)

def load_schema():
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)

def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

def test_required_fields_present():
    schema = load_schema()
    props = schema["properties"]
    for field in [
        "smiles",
        "node_features",
        "edge_features",
        "surface_area",
        "molecular_weight",
    ]:
        assert field in props, f"Missing field: {field}"

def test_surface_area_is_required_and_numeric():
    schema = load_schema()
    assert "surface_area" in schema["required"]
    assert schema["properties"]["surface_area"]["type"] == "number"
    assert schema["properties"]["surface_area"]["minimum"] == 0

def test_smiles_is_required_string():
    schema = load_schema()
    assert "smiles" in schema["required"]
    assert schema["properties"]["smiles"]["type"] == "string"