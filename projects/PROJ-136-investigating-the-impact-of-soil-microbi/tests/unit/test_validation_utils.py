import pytest
import pandas as pd
from pathlib import Path
from code.analysis.validation_utils import validate_record, validate_dataframe_records, load_schema

# Use the contracts created in T004
SAMPLE_SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "sample.schema.yaml"

def test_load_schema():
    schema = load_schema(SAMPLE_SCHEMA_PATH)
    assert "type" in schema
    assert schema["type"] == "object"

def test_validate_valid_record():
    schema = load_schema(SAMPLE_SCHEMA_PATH)
    valid_record = {
        "sample_id": "S0001",
        "plant_species": "Zea mays",
        "gps_latitude": 40.0,
        "gps_longitude": -74.0,
        "soil_type": "loam",
        "sequencing_depth": 50000
    }
    assert validate_record(valid_record, schema) is True

def test_validate_invalid_record():
    schema = load_schema(SAMPLE_SCHEMA_PATH)
    invalid_record = {
        "sample_id": "S0001",
        "plant_species": "Zea mays",
        "gps_latitude": 100.0, # Invalid latitude
        "gps_longitude": -74.0,
        "soil_type": "loam",
        "sequencing_depth": 50000
    }
    with pytest.raises(Exception): # ValidationError
        validate_record(invalid_record, schema)

def test_validate_dataframe():
    schema = load_schema(SAMPLE_SCHEMA_PATH)
    df = pd.DataFrame([
        {
            "sample_id": "S0001",
            "plant_species": "Zea mays",
            "gps_latitude": 40.0,
            "gps_longitude": -74.0,
            "soil_type": "loam",
            "sequencing_depth": 50000
        },
        {
            "sample_id": "S0002",
            "plant_species": "Zea mays",
            "gps_latitude": 100.0, # Invalid
            "gps_longitude": -74.0,
            "soil_type": "loam",
            "sequencing_depth": 50000
        }
    ])
    errors = validate_dataframe_records(df, schema)
    assert len(errors) == 1
    assert errors[0]["row_index"] == 1