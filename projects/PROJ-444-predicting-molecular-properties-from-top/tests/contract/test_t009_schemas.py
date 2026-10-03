import yaml
import os
import sys
from pathlib import Path

# Add project root to path to allow imports if needed, though this is a standalone test
project_root = Path(__file__).parent.parent.parent
contracts_dir = project_root / "specs" / "001-predict-molecular-properties-tda" / "contracts"

def test_dataset_schema_exists_and_valid():
    """Verify dataset.schema.yaml exists, is valid YAML, and contains required fields."""
    schema_path = contracts_dir / "dataset.schema.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "required" in schema, "Schema must define required fields"
    assert "molecule_id" in schema["required"], "molecule_id must be required"
    assert "smiles" in schema["required"], "smiles must be required"
    assert "logP" in schema["required"], "logP must be required"
    assert "properties" in schema, "Schema must define properties"

def test_feature_matrix_schema_exists_and_valid():
    """Verify feature_matrix.schema.yaml exists, is valid YAML, and contains required fields."""
    schema_path = contracts_dir / "feature_matrix.schema.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "required" in schema, "Schema must define required fields"
    assert "molecule_id" in schema["required"], "molecule_id must be required"
    assert "resolution" in schema["properties"], "resolution property must exist"
    assert "p_img_columns" in schema["properties"], "p_img_columns property must exist"

def test_model_metrics_schema_exists_and_valid():
    """Verify model_metrics.schema.yaml exists, is valid YAML, and contains required fields."""
    schema_path = contracts_dir / "model_metrics.schema.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "required" in schema, "Schema must define required fields"
    assert "traditional" in schema["required"], "traditional metrics must be required"
    assert "topological" in schema["required"], "topological metrics must be required"
    assert "combined" in schema["required"], "combined metrics must be required"
    assert "feature_importance" in schema["required"], "feature_importance must be required"
    
    # Check for methodology metadata as per T028
    if "properties" in schema:
        assert "methodology" in schema["properties"], "methodology property should be defined"

def test_all_schemas_are_valid_yaml():
    """Ensure all three schema files are syntactically valid YAML."""
    schema_files = [
        "dataset.schema.yaml",
        "feature_matrix.schema.yaml",
        "model_metrics.schema.yaml"
    ]
    
    for filename in schema_files:
        filepath = contracts_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {filename}: {e}")
        else:
            pytest.fail(f"File missing: {filename}")