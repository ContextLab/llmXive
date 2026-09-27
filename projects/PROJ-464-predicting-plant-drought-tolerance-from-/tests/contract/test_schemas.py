import os
import sys
import pytest
import pandas as pd
import json
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError

# Add project root to path for imports if needed, though we are testing files directly
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

SCHEMA_FILES = [
    "dataset.schema.yaml",
    "rsametrics.schema.yaml",
    "merged_data.schema.yaml",
    "model_results.schema.yaml",
    "output.schema.yaml",
    "results.schema.yaml"
]

def load_schema(schema_name: str) -> dict:
    path = CONTRACTS_DIR / schema_name
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_rsametrics():
    return pd.DataFrame({
        "species_id": ["A", "B"],
        "depth": [10.5, 12.0],
        "branching_density": [0.5, 0.8],
        "surface_area": [100.0, 150.0]
    })

@pytest.fixture
def sample_merged_data():
    return pd.DataFrame({
        "species_id": ["A", "B"],
        "depth": [10.5, 12.0],
        "branching_density": [0.5, 0.8],
        "surface_area": [100.0, 150.0],
        "stomatal_conductance": [0.2, 0.3],
        "photosynthesis": [10.0, 12.0],
        "pca_depth": [1.0, 2.0],
        "pca_branching": [0.1, 0.2],
        "pca_surface": [5.0, 6.0],
        "pvr_lambda": [0.5, 0.6],
        "survival_rate": [0.9, 0.8]
    })

@pytest.fixture
def sample_model_results():
    return pd.DataFrame({
        "model_type": ["OLS", "Ridge"],
        "predictor": ["depth", "depth"],
        "coefficient": [0.5, 0.4],
        "p_value": [0.01, 0.02],
        "r2": [0.6, 0.65],
        "adj_p_value": [0.02, 0.04],
        "vif_score": [2.0, 2.1]
    })

@pytest.fixture
def sample_sensitivity_results():
    return pd.DataFrame({
        "threshold": [0.5, 0.6],
        "accuracy": [0.8, 0.79],
        "precision": [0.82, 0.85],
        "recall": [0.75, 0.70],
        "f1_score": [0.78, 0.76],
        "false_positive_rate": [0.1, 0.08],
        "false_negative_rate": [0.25, 0.30]
    })

def validate_dataframe_against_schema(df: pd.DataFrame, schema: dict):
    # Convert dataframe to list of dicts for JSON schema validation
    # JSON schema validates a single object, so we validate the first row
    # or iterate if the schema expects an array of objects.
    # For this project, schemas are defined for a single record (row).
    if len(df) == 0:
        pytest.fail("DataFrame is empty, cannot validate.")
    
    # Validate first row
    record = df.iloc[0].to_dict()
    try:
        validate(instance=record, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Validation failed for row 0: {e.message}")

def test_schema_files_exist():
    for name in SCHEMA_FILES:
        assert (CONTRACTS_DIR / name).exists(), f"Missing schema: {name}"

def test_rsametrics_schema_valid(sample_rsametrics):
    schema = load_schema("rsametrics.schema.yaml")
    validate_dataframe_against_schema(sample_rsametrics, schema)

def test_rsametrics_schema_rejects_invalid():
    schema = load_schema("rsametrics.schema.yaml")
    invalid_df = pd.DataFrame({
        "species_id": ["A"],
        "depth": [-5.0], # Must be positive
        "branching_density": [0.5],
        "surface_area": [100.0]
    })
    record = invalid_df.iloc[0].to_dict()
    with pytest.raises(ValidationError):
        validate(instance=record, schema=schema)

def test_merged_data_schema_valid(sample_merged_data):
    schema = load_schema("merged_data.schema.yaml")
    validate_dataframe_against_schema(sample_merged_data, schema)

def test_model_results_schema_valid(sample_model_results):
    schema = load_schema("model_results.schema.yaml")
    validate_dataframe_against_schema(sample_model_results, schema)

def test_sensitivity_results_schema_valid(sample_sensitivity_results):
    schema = load_schema("results.schema.yaml")
    validate_dataframe_against_schema(sample_sensitivity_results, schema)

def test_output_schema_structure():
    schema = load_schema("output.schema.yaml")
    # Just validate the schema structure is valid JSON Schema
    jsonschema.Draft7Validator.check_schema(schema)
    # Check required fields
    assert "report_title" in schema["required"]
    assert "summary" in schema["required"]
    assert "tolerance_proxy_status" in schema["required"]