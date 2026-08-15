"""
Unit tests for Pydantic schemas and YAML export.
"""
import pytest
import yaml
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from contracts.schemas import (
    CeramicEntry, 
    DescriptorSet, 
    ModelResult, 
    export_schemas_to_yaml, 
    load_schema, 
    validate_schemas, 
    validate_data_against_schema
)

def test_ceramic_entry_creation():
    """Test creating a valid CeramicEntry instance."""
    data = {
        "composition": "Al2O3",
        "weibull_modulus": 15.5,
        "sample_count": 50,
        "primary_anion_cation_group": "O-Al"
    }
    entry = CeramicEntry(**data)
    assert entry.composition == "Al2O3"
    assert entry.weibull_modulus == 15.5
    assert entry.sample_count == 50
    assert entry.is_range_flag == False

def test_ceramic_entry_with_optional_fields():
    """Test CeramicEntry with optional fields populated."""
    data = {
        "composition": "ZrO2",
        "weibull_modulus": 12.0,
        "sample_count": 35,
        "primary_anion_cation_group": "O-Zr",
        "sintering_temp": 1500.0,
        "is_imputed": False,
        "mean_atomic_radius": 1.5,
        "electronegativity_std": 0.2,
        "valence_electron_concentration": 4.0
    }
    entry = CeramicEntry(**data)
    assert entry.sintering_temp == 1500.0
    assert entry.mean_atomic_radius == 1.5

def test_descriptor_set_creation():
    """Test creating a valid DescriptorSet instance."""
    data = {
        "descriptors": ["mean_radius", "electroneg_std"],
        "values": {"mean_radius": 1.2, "electroneg_std": 0.5},
        "source": "test_source"
    }
    ds = DescriptorSet(**data)
    assert len(ds.descriptors) == 2
    assert ds.source == "test_source"

def test_model_result_creation():
    """Test creating a valid ModelResult instance."""
    data = {
        "model_type": "RandomForest",
        "mae": 2.5,
        "r_squared": 0.85,
        "feature_importance_ranking": [{"feature": "f1", "score": 0.9}],
        "cv_stability_scores": {"mean": 0.9, "std": 0.1}
    }
    result = ModelResult(**data)
    assert result.model_type == "RandomForest"
    assert result.mae == 2.5

def test_export_schemas_to_yaml():
    """Test that export_schemas_to_yaml creates the expected files."""
    output_dir = "code/contracts"
    export_schemas_to_yaml(output_dir)
    
    assert Path(f"{output_dir}/ceramic_entry.schema.yaml").exists()
    assert Path(f"{output_dir}/model_result.schema.yaml").exists()

    # Verify content is valid YAML
    with open(f"{output_dir}/ceramic_entry.schema.yaml") as f:
        schema = yaml.safe_load(f)
        assert "properties" in schema
        assert "composition" in schema["properties"]

    with open(f"{output_dir}/model_result.schema.yaml") as f:
        schema = yaml.safe_load(f)
        assert "properties" in schema
        assert "model_type" in schema["properties"]

def test_load_schema():
    """Test loading a schema from YAML."""
    schema = load_schema("ceramic_entry")
    assert "properties" in schema
    assert schema["properties"]["composition"]["type"] == "string"

def test_validate_schemas():
    """Test the validate_schemas function."""
    # First ensure schemas are exported
    export_schemas_to_yaml()
    assert validate_schemas() is True

def test_validate_data_against_schema_valid():
    """Test validating valid data against schema."""
    data = {
        "composition": "SiC",
        "weibull_modulus": 10.0,
        "sample_count": 40,
        "primary_anion_cation_group": "C-Si"
    }
    assert validate_data_against_schema(data, "ceramic_entry") is True

def test_validate_data_against_schema_invalid():
    """Test validating invalid data against schema."""
    # Missing required field 'composition'
    data = {
        "weibull_modulus": 10.0,
        "sample_count": 40,
        "primary_anion_cation_group": "C-Si"
    }
    assert validate_data_against_schema(data, "ceramic_entry") is False
