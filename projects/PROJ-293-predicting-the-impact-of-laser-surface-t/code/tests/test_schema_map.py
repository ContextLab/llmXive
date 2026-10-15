import json
import yaml
from pathlib import Path

# Load the canonical schema definition (assumed to be in specs/001-predicting-the-impact-of-laser-surface-t/data-model.md)
# For this test we just need to ensure that the keys exist in the schema_map.json

def test_schema_map_keys():
    schema_map_path = Path("code/config/schema_map.json")
    assert schema_map_path.exists(), f"{schema_map_path} does not exist"

    with schema_map_path.open("r", encoding="utf-8") as f:
        schema_map = json.load(f)

    # The canonical keys we expect (based on the dataset schema) – this list should be
    # aligned with the actual dataset schema used in the project.
    expected_keys = [
        "pulse_duration",
        "power",
        "scanning_speed",
        "pattern_geometry",
        "hardness",
        "elastic_modulus",
        "wear_rate",
        "contact_load",
        "sliding_speed",
        "density",
        "geometry"
    ]

    for key in expected_keys:
        assert key in schema_map, f"Canonical key {key} missing from schema_map.json"
