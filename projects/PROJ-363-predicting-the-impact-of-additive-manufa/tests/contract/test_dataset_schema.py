import pytest
import pandas as pd
import jsonschema
import yaml
from pathlib import Path


@pytest.fixture
def schema():
    with open("contracts/dataset.schema.yaml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def cleaned_data():
    # Placeholder for actual data loading
    return pd.DataFrame({
        "laser_power": [100.0],
        "scan_speed": [500.0],
        "hatch_spacing": [100.0],
        "layer_thickness": [30.0],
        "porosity": [0.1],
    })


def test_dataset_schema_valid(schema, cleaned_data):
    """Validate cleaned dataset against schema."""
    # Convert DataFrame to dict for schema validation
    data_dict = {
        "columns": [{"name": col, "type": "numeric", "required": True} for col in cleaned_data.columns],
        "required_columns": list(cleaned_data.columns),
    }

    # Basic validation (expand as needed)
    required_cols = schema.get("required_columns", [])
    for col in required_cols:
        assert col in cleaned_data.columns, f"Missing required column: {col}"
