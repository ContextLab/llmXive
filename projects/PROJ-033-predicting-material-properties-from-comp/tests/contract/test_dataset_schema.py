"""Contract tests for contracts/materials_dataset.schema.yaml."""

import json
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "materials_dataset.schema.yaml"


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def valid_row(**overrides):
    row = {
        "material_id": "mp-1",
        "formula": "Fe2O3",
        "band_gap": 1.7,
        "hardness": 9.5,
        "crystal_system": "hexagonal",
    }
    row.update(overrides)
    return row


def test_schema_file_exists_and_parses():
    assert SCHEMA_PATH.exists(), f"missing schema: {SCHEMA_PATH}"
    schema = load_schema()
    assert schema["title"] == "Materials property dataset contract"
    Draft7Validator.check_schema(schema)


def test_schema_requires_all_five_columns():
    schema = load_schema()
    required = set(schema["items"]["required"])
    assert required == {
        "material_id",
        "formula",
        "band_gap",
        "hardness",
        "crystal_system",
    }


def test_valid_rows_pass():
    validator = Draft7Validator(load_schema())
    rows = [
        valid_row(),
        valid_row(material_id="mp-2", formula="Si", band_gap=0, hardness=0.0,
                  crystal_system="cubic"),  # zero-band-gap metal retained
    ]
    for row in rows:
        errors = list(validator.iter_errors(row))
        assert not errors, f"unexpected errors: {errors}"


def test_missing_required_field_fails():
    validator = Draft7Validator(load_schema())
    for field in ["material_id", "formula", "band_gap", "hardness", "crystal_system"]:
        row = valid_row()
        del row[field]
        errors = list(validator.iter_errors(row))
        assert errors, f"row missing {field} should fail validation"


def test_invalid_values_fail():
    validator = Draft7Validator(load_schema())
    bad_rows = [
        valid_row(band_gap=-0.5),          # negative band gap
        valid_row(hardness=-1.0),          # negative hardness
        valid_row(crystal_system="banana"),  # not one of the 7 systems
        valid_row(formula="x"),            # too short
        valid_row(material_id=""),         # empty ID
    ]
    for row in bad_rows:
        errors = list(validator.iter_errors(row))
        assert errors, f"row {row} should fail validation"


def test_crystal_system_enum_is_seven_systems():
    schema = load_schema()
    enum = schema["items"]["properties"]["crystal_system"]["enum"]
    assert set(enum) == {
        "triclinic", "monoclinic", "orthorhombic", "tetragonal",
        "trigonal", "hexagonal", "cubic",
    }
