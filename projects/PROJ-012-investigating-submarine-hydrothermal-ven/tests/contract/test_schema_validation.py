"""
Contract tests for data schema validation.
Validates that generated artifacts conform to the defined YAML schemas.
"""
import json
import os
import yaml
import pandas as pd
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Path to the project root (assumed to be two levels up from tests/contract)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

@pytest.fixture
def sample_schema():
    with open(CONTRACTS_DIR / "sample_schema.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def otu_schema():
    with open(CONTRACTS_DIR / "otu_table_schema.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def analysis_schema():
    with open(CONTRACTS_DIR / "analysis_results_schema.schema.yaml", "r") as f:
        return yaml.safe_load(f)

def load_csv_as_json(path):
    """Load a CSV file and return it as a list of dicts (JSON-compatible)."""
    if not os.path.exists(path):
        pytest.skip(f"File not found: {path}")
    df = pd.read_csv(path)
    return df.to_dict(orient="records")

def validate_record(record, schema, record_name):
    """Validate a single record against a schema."""
    try:
        validate(instance=record, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Validation failed for {record_name}: {e.message} at {e.path}")

@pytest.mark.contract
def test_unified_sample_table_schema(sample_schema):
    """Validates unified_sample_table.csv against sample_schema.schema.yaml"""
    file_path = PROJECT_ROOT / "data/processed/unified_sample_table.csv"
    records = load_csv_as_json(file_path)
    
    if not records:
        pytest.skip("No records to validate in unified_sample_table.csv")

    for i, record in enumerate(records):
        validate_record(record, sample_schema, f"sample_record_{i}")

@pytest.mark.contract
def test_alpha_diversity_results_schema(analysis_schema):
    """Validates alpha_diversity_results.csv against analysis_results_schema.schema.yaml"""
    file_path = PROJECT_ROOT / "data/processed/alpha_diversity_results.csv"
    records = load_csv_as_json(file_path)
    
    if not records:
        pytest.skip("No records to validate in alpha_diversity_results.csv")

    for i, record in enumerate(records):
        validate_record(record, analysis_schema, f"diversity_record_{i}")

@pytest.mark.contract
def test_lme_results_schema(analysis_schema):
    """Validates lme_results.csv against analysis_results_schema.schema.yaml"""
    file_path = PROJECT_ROOT / "data/processed/lme_results.csv"
    records = load_csv_as_json(file_path)
    
    if not records:
        pytest.skip("No records to validate in lme_results.csv")

    for i, record in enumerate(records):
        validate_record(record, analysis_schema, f"lme_record_{i}")

@pytest.mark.contract
def test_beta_diversity_results_schema(analysis_schema):
    """Validates beta_diversity_results.csv against analysis_results_schema.schema.yaml"""
    file_path = PROJECT_ROOT / "data/processed/beta_diversity_results.csv"
    records = load_csv_as_json(file_path)
    
    if not records:
        pytest.skip("No records to validate in beta_diversity_results.csv")

    for i, record in enumerate(records):
        validate_record(record, analysis_schema, f"beta_record_{i}")
