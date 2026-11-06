"""
Unit test for ``code.utils.validate_schemas.validate``.

The test loads a minimal compliant record and validates it against the
``ingest.schema.yaml`` and ``dataset.schema.yaml`` contracts. Both schemas
are provided under ``specs/001-predicting-corrosion-potential-from-comp/contracts``.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths
from code.utils.validate_schemas import validate
from jsonschema.exceptions import ValidationError

# Helper to load a schema path from the specs directory
def _schema_path(name: str) -> Path:
    return Path(
        paths.root,
        "specs",
        "001-predict-corrosion-potential-from-comp",
        "contracts",
        name,
    )

def test_validate_ingest_schema():
    # Minimal record that satisfies the ingest schema
    record = {
        "record_id": "R001",
        "alloy_designation": "SS304",
        "composition": {"Fe": 0.7, "Cr": 0.2, "Ni": 0.1},
        "ph": 7.0,
        "temperature_celsius": 25.0,
        "corrosion_potential_mV": -150.0,
    }
    schema_path = _schema_path("ingest.schema.yaml")
    # Should not raise
    validate(record, schema_path)

def test_validate_dataset_schema():
    # Minimal record that satisfies the processed dataset schema
    record = {
        "record_id": "R001",
        "alloy_designation": "SS304",
        "ph": 7.0,
        "temperature_celsius": 25.0,
        "corrosion_potential_mV": -150.0,
        "composition_clr": [0.1, -0.2, 0.3],
        "electrolyte_type_onehot": [1, 0],
    }
    schema_path = _schema_path("dataset.schema.yaml")
    # Should not raise
    validate(record, schema_path)

def test_invalid_record_raises():
    # Missing required field 'ph' – should raise ValidationError
    record = {
        "record_id": "R001",
        "alloy_designation": "SS304",
        "composition": {"Fe": 0.7},
        "temperature_celsius": 25.0,
        "corrosion_potential_mV": -150.0,
    }
    schema_path = _schema_path("ingest.schema.yaml")
    try:
        validate(record, schema_path)
    except ValidationError:
        assert True
    else:
        assert False, "ValidationError expected for incomplete record"