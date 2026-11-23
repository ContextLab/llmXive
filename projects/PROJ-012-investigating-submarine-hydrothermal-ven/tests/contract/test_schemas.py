"""
Contract tests for data schemas defined in contracts/.
Validates that generated CSVs match the YAML schema definitions.
"""
import json
import os
import pytest
import pandas as pd
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

SCHEMA_FILES = {
    "sample": "sample_schema.schema.yaml",
    "otu": "otu_table_schema.schema.yaml",
    "analysis": "analysis_results_schema.schema.yaml",
}

@pytest.fixture(scope="module")
def schemas():
    """Load all YAML schemas."""
    loaded_schemas = {}
    for key, filename in SCHEMA_FILES.items():
        path = CONTRACTS_DIR / filename
        if not path.exists():
            pytest.fail(f"Schema file not found: {path}")
        with open(path, "r") as f:
            loaded_schemas[key] = yaml.safe_load(f)
    return loaded_schemas

def validate_dataframe(df: pd.DataFrame, schema: dict, name: str):
    """Validate a DataFrame against a JSON schema."""
    # Convert DataFrame to list of dicts for validation
    records = df.to_dict(orient="records")
    
    # Check required columns exist
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in df.columns:
            raise AssertionError(f"Missing required column '{field}' in {name}")

    # Validate each row (simplified for performance, ideally sample)
    for i, record in enumerate(records):
        try:
            validate(instance=record, schema=schema)
        except ValidationError as e:
            raise AssertionError(
                f"Validation error in {name}, row {i}: {e.message} "
                f"(Path: {e.absolute_path})"
            )

@pytest.mark.contract
def test_sample_schema(schemas):
    """Test unified_sample_table.csv against sample_schema."""
    # Check if file exists (skip if not generated yet)
    file_path = PROJECT_ROOT / "data" / "processed" / "unified_sample_table.csv"
    if not file_path.exists():
        pytest.skip("unified_sample_table.csv not found. Run ingestion pipeline first.")
    
    df = pd.read_csv(file_path)
    validate_dataframe(df, schemas["sample"], "Sample Table")

@pytest.mark.contract
def test_otu_schema(schemas):
    """Test OTU table against otu_table_schema."""
    file_path = PROJECT_ROOT / "data" / "processed" / "otu_table.csv"
    if not file_path.exists():
        pytest.skip("otu_table.csv not found. Run preprocessing pipeline first.")
    
    df = pd.read_csv(file_path)
    validate_dataframe(df, schemas["otu"], "OTU Table")

@pytest.mark.contract
def test_analysis_schema(schemas):
    """Test analysis results against analysis_results_schema."""
    file_path = PROJECT_ROOT / "data" / "processed" / "lme_results.csv"
    if not file_path.exists():
        pytest.skip("lme_results.csv not found. Run analysis pipeline first.")
    
    df = pd.read_csv(file_path)
    validate_dataframe(df, schemas["analysis"], "Analysis Results")
