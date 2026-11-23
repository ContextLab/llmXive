"""
Tests for the ingest module.
"""
import pytest
import os
import tempfile
import json
from pathlib import Path
import pandas as pd
import yaml

# Add parent directory to path to import code modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import (
    load_manifest,
    validate_manifest,
    process_manifest_entry,
    verify_dataset_variables,
    ingest_pipeline
)

# Create a temporary directory for test artifacts
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_manifest_csv(temp_dir):
    manifest_path = temp_dir / "manifest.csv"
    data = [
        {
            "doi": "10.1038/test001",
            "dataset_name": "Test Dataset",
            "dataset_url": "https://example.com/data.csv",
            "dataset_type": "csv",
            "reported_metrics": {"mae": 10.0, "r2": 0.5, "rho": 0.4},
            "notes": "Test entry"
        }
    ]
    df = pd.DataFrame(data)
    df.to_csv(manifest_path, index=False)
    return manifest_path

@pytest.fixture
def sample_schema_yaml(temp_dir):
    schema_path = temp_dir / "schema.yaml"
    schema = {
        "type": "object",
        "required": ["doi", "dataset_name", "dataset_url", "reported_metrics"],
        "properties": {
            "doi": {"type": "string", "pattern": "^10\\.[0-9]{4,}/[^\\s]+$"},
            "dataset_name": {"type": "string"},
            "dataset_url": {"type": "string", "format": "uri"},
            "dataset_type": {"type": "string"},
            "reported_metrics": {
                "type": "object",
                "required": ["mae", "r2", "rho"],
                "properties": {
                    "mae": {"type": "number"},
                    "r2": {"type": "number"},
                    "rho": {"type": "number"}
                }
            },
            "notes": {"type": "string"}
        }
    }
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)
    return schema_path

def test_load_manifest(sample_manifest_csv):
    manifest = load_manifest(sample_manifest_csv)
    assert len(manifest) == 1
    assert manifest[0]['doi'] == "10.1038/test001"

def test_validate_manifest_valid(sample_manifest_csv, sample_schema_yaml):
    manifest = load_manifest(sample_manifest_csv)
    is_valid, errors = validate_manifest(manifest, sample_schema_yaml)
    assert is_valid
    assert len(errors) == 0

def test_validate_manifest_invalid_doi(temp_dir, sample_schema_yaml):
    # Create manifest with invalid DOI
    manifest_path = temp_dir / "invalid_manifest.csv"
    data = [
        {
            "doi": "invalid-doi",
            "dataset_name": "Test",
            "dataset_url": "https://example.com/data.csv",
            "dataset_type": "csv",
            "reported_metrics": {"mae": 10.0, "r2": 0.5, "rho": 0.4}
        }
    ]
    df = pd.DataFrame(data)
    df.to_csv(manifest_path, index=False)
    
    manifest = load_manifest(manifest_path)
    is_valid, errors = validate_manifest(manifest, sample_schema_yaml)
    assert not is_valid
    assert any("Invalid DOI" in err for err in errors)

def test_verify_dataset_variables(temp_dir):
    # Create a dummy CSV
    csv_path = temp_dir / "data.csv"
    df = pd.DataFrame({"smiles": ["CCO"], "yield": [90.0]})
    df.to_csv(csv_path, index=False)
    
    valid, missing = verify_dataset_variables(csv_path, ["smiles", "yield"])
    assert valid
    assert len(missing) == 0
    
    valid, missing = verify_dataset_variables(csv_path, ["smiles", "temperature"])
    assert not valid
    assert "temperature" in missing

def test_ingest_pipeline_missing_manifest(temp_dir):
    result = ingest_pipeline(manifest_path=temp_dir / "nonexistent.csv")
    assert result['status'] == 'failed'
    assert "not found" in result['error'].lower()