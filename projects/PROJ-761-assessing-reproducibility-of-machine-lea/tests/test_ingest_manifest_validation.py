import os
import sys
import pytest
import yaml
import json
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingest import load_manifest, validate_manifest

@pytest.fixture
def temp_manifest_file(tmp_path):
    manifest = {
        "papers": [
            {
                "doi": "10.1021/acscatal.0c01234",
                "dataset_name": "TestDataset",
                "reported_metrics": {"mae": 0.1, "r2": 0.9}
            }
        ]
    }
    file_path = tmp_path / "manifest.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(manifest, f)
    return str(file_path)

@pytest.fixture
def temp_schema_file(tmp_path):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["papers"],
        "properties": {
            "papers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["doi", "dataset_name", "reported_metrics"],
                    "properties": {
                        "doi": {"type": "string"},
                        "dataset_name": {"type": "string"},
                        "reported_metrics": {"type": "object"}
                    }
                }
            }
        }
    }
    file_path = tmp_path / "schema.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(schema, f)
    return str(file_path)

def test_load_manifest_success(temp_manifest_file):
    manifest = load_manifest(temp_manifest_file)
    assert 'papers' in manifest
    assert len(manifest['papers']) == 1
    assert manifest['papers'][0]['doi'] == "10.1021/acscatal.0c01234"

def test_validate_manifest_success(temp_manifest_file, temp_schema_file):
    manifest = load_manifest(temp_manifest_file)
    is_valid, errors = validate_manifest(manifest, temp_schema_file)
    assert is_valid
    assert len(errors) == 0

def test_validate_manifest_failure(temp_manifest_file, temp_schema_file):
    # Modify manifest to be invalid
    manifest = load_manifest(temp_manifest_file)
    manifest['papers'][0].pop('doi') # Remove required field
    
    is_valid, errors = validate_manifest(manifest, temp_schema_file)
    assert not is_valid
    assert len(errors) > 0
    assert any("doi" in err for err in errors)