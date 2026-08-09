import pytest
import yaml
import tempfile
import os
from pathlib import Path
from jsonschema import ValidationError
from analysis.validation_utils import load_schema, validate_record

@pytest.fixture
def schema():
    return load_schema("disease-incidence.schema.yaml")

def test_disease_incidence_schema_structure(schema):
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert len(schema["properties"]) > 0

def test_disease_incidence_schema_validates_correct_record(schema):
    record = {
        "sample_id": "S123",
        "plant_species": "Tomato",
        "gps_coordinates": [37.7749, -122.4194],
        "soil_type": "Loam",
        "disease_incidence": 0.5,
        "measurement_date": "2024-01-01"
    }
    validate_record(record, schema)

def test_disease_incidence_schema_rejects_missing_required(schema):
    record = {
        "plant_species": "Tomato",
        "gps_coordinates": [37.7749, -122.4194],
        "soil_type": "Loam",
        "disease_incidence": 0.5
    }
    with pytest.raises(ValidationError):
        validate_record(record, schema)

def test_disease_incidence_schema_rejects_invalid_range(schema):
    record = {
        "sample_id": "S123",
        "plant_species": "Tomato",
        "gps_coordinates": [37.7749, -122.4194],
        "soil_type": "Loam",
        "disease_incidence": 1.5,
        "measurement_date": "2024-01-01"
    }
    with pytest.raises(ValidationError):
        validate_record(record, schema)

def test_disease_incidence_schema_validates_dataframe(schema):
  import pandas as pd
  data = [
      {"sample_id": "S1", "plant_species": "Tomato", "gps_coordinates": [37.7749, -122.4194], "soil_type": "Loam", "disease_incidence": 0.5, "measurement_date": "2024-01-01"},
      {"sample_id": "S2", "plant_species": "Potato", "gps_coordinates": [34.0522, -118.2437], "soil_type": "Sandy", "disease_incidence": 0.2, "measurement_date": "2024-02-15"}
  ]
  df = pd.DataFrame(data)
  try:
    validate_dataframe_records(df, schema)
  except ValidationError as e:
      assert False, f"Validation failed for dataframe: {e}"