import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

# Load schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "taxon.schema.yaml"

def load_yaml_schema(path):
    """Simple YAML loader for the schema file."""
    with open(path, 'r') as f:
        content = f.read()
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        pytest.skip("PyYAML not installed")

schema = load_yaml_schema(SCHEMA_PATH)

def test_valid_taxon():
    valid_data = {
        "taxon_id": "T0001",
        "sample_id": "S0001",
        "kingdom": "Bacteria",
        "phylum": "Proteobacteria",
        "class": "Gammaproteobacteria",
        "order": "Pseudomonadales",
        "family": "Pseudomonadaceae",
        "genus": "Pseudomonas",
        "species": "P. fluorescens",
        "abundance": 1500,
        "relative_abundance": 0.03,
        "confidence_score": 0.95
    }
    validate(instance=valid_data, schema=schema)

def test_invalid_taxon_missing_required():
    invalid_data = {
        "taxon_id": "T0001",
        "sample_id": "S0001",
        "kingdom": "Bacteria"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_invalid_taxon_abundance_negative():
    invalid_data = {
        "taxon_id": "T0001",
        "sample_id": "S0001",
        "kingdom": "Bacteria",
        "phylum": "Proteobacteria",
        "class": "Gammaproteobacteria",
        "order": "Pseudomonadales",
        "family": "Pseudomonadaceae",
        "genus": "Pseudomonas",
        "species": "P. fluorescens",
        "abundance": -10,
        "relative_abundance": 0.03,
        "confidence_score": 0.95
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)
