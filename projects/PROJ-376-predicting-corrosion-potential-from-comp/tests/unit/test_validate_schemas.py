"""
Unit test for ``code.utils.validate_schemas`` (T005).

The test constructs a minimal, schema‑compliant record and validates it
against both the ingest and dataset schemas. No exception should be raised.
"""

import pytest
from pathlib import Path

from code.utils.validate_schemas import validate

# Paths to the schema files defined in the specs directory.
INGEST_SCHEMA = Path(
    "specs",
    "001-predict-corrosion-potential-from-comp",
    "contracts",
    "ingest.schema.yaml",
)
DATASET_SCHEMA = Path(
    "specs",
    "001-predict-corrosion-potential-from-comp",
    "contracts",
    "dataset.schema.yaml",
)

def test_validate_ingest_schema():
    sample = {
        "alloy_designation": "SS304",
        "composition": {"Fe": 0.70, "Cr": 0.19, "Ni": 0.11},
        "ph": 7.0,
        "temperature_celsius": 25.0,
        "corrosion_potential_mV": -150.0,
        "electrolyte_type": "NaCl",
    }
    # Should not raise
    validate(sample, INGEST_SCHEMA)

def test_validate_dataset_schema():
    # After processing, elemental columns are flattened.
    sample = {
        "alloy_designation": "SS304",
        "ph": 7.0,
        "temperature_celsius": 25.0,
        "corrosion_potential_mV": -150.0,
        "electrolyte_type": "NaCl",
        "Fe": 0.7,
        "Cr": 0.19,
        "Ni": 0.11,
        "Al": 0.0,
        "Ti": 0.0,
    }
    validate(sample, DATASET_SCHEMA)
