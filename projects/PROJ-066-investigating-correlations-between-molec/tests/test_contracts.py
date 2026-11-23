import pytest
import yaml
from pathlib import Path

def test_molecule_schema_exists():
    """Verifies the molecule schema file exists and is valid YAML."""
    schema_path = Path("contracts/molecule.schema.yaml")
    assert schema_path.exists(), "molecule.schema.yaml must exist"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert "properties" in schema
    assert "SMILES" in schema["properties"]
    assert "target" in schema["properties"]
    assert "experimental_value" in schema["properties"]

def test_model_output_schema_exists():
    """Verifies the model output schema file exists and is valid YAML."""
    schema_path = Path("contracts/model_output.schema.yaml")
    assert schema_path.exists(), "model_output.schema.yaml must exist"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert "properties" in schema
    assert "metrics" in schema["properties"]
    assert "rmse" in schema["properties"]["metrics"]["properties"]
    assert "baseline_rmse" in schema["properties"]["metrics"]["properties"]