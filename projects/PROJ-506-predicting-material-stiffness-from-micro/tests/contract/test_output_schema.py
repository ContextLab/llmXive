"""
Contract test for model output schema validation.
"""
import pytest
import yaml
from pathlib import Path

def test_output_schema_exists():
    schema_path = Path("specs/001-predict-stiffness-cnn/contracts/model-output.schema.yaml")
    assert schema_path.exists(), "Model output schema file missing"

def test_output_schema_valid():
    schema_path = Path("specs/001-predict-stiffness-cnn/contracts/model-output.schema.yaml")
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    assert "properties" in schema
    assert "model_version" in schema["properties"]
    assert "prediction" in schema["properties"]
    assert "error" in schema["properties"]
    assert "density_bin" in schema["properties"]
