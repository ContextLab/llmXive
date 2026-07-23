import os
import sys
import json
import yaml
from pathlib import Path
import pytest

# Add project root to path if needed (assuming standard layout)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-chemo-biomarker-discovery" / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a schema file from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: any, expected_type: str) -> bool:
    """Basic type validation helper."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    if expected_type not in type_map:
        return True
    return isinstance(value, type_map[expected_type])

def validate_required_fields(data: dict, required_fields: list, path: str = "") -> list:
    """Recursively check for required fields."""
    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(f"{path}.{field}" if path else field)
    return missing

def validate_data_against_schema(data: dict, schema: dict, path: str = "") -> list:
    """Validate data against a JSON schema definition (simplified)."""
    errors = []
    
    # Check required fields
    if "required" in schema:
        missing = validate_required_fields(data, schema["required"], path)
        errors.extend(missing)
    
    # Check properties
    if "properties" in schema:
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                value = data[prop]
                
                # Type check
                if "type" in prop_schema:
                    if not validate_type(value, prop_schema["type"]):
                        errors.append(f"{path}.{prop}: expected {prop_schema['type']}, got {type(value).__name__}")
                
                # Nested object check
                if prop_schema.get("type") == "object" and "properties" in prop_schema:
                    nested_errors = validate_data_against_schema(value, prop_schema, f"{path}.{prop}")
                    errors.extend(nested_errors)
                
                # Array check
                if prop_schema.get("type") == "array" and "items" in prop_schema:
                    if isinstance(value, list):
                        item_schema = prop_schema["items"]
                        for i, item in enumerate(value):
                            if item_schema.get("type") == "object" and "properties" in item_schema:
                                item_errors = validate_data_against_schema(item, item_schema, f"{path}.{prop}[{i}]")
                                errors.extend(item_errors)
    return errors

@pytest.fixture
def sample_dataset_data():
    """Generate valid sample data for dataset schema."""
    return {
        "metadata": {
            "source": "TCGA-BRCA",
            "tumor_type": "BRCA",
            "processing_date": "2023-10-01T12:00:00Z",
            "version": "1.0.0",
            "sample_count": 100,
            "gene_count": 20000,
            "response_distribution": {
                "responders": 40,
                "non_responders": 60
            }
        },
        "samples": [
            {"sample_id": "S1", "response_label": "responder", "platform": "Illumina", "batch_id": "B1"},
            {"sample_id": "S2", "response_label": "non_responder", "platform": "Illumina", "batch_id": "B1"}
        ],
        "features": [
            {"gene_symbol": "TP53", "biotype": "protein_coding"},
            {"gene_symbol": "BRCA1", "biotype": "protein_coding"}
        ],
        "expression_data": {
            "S1": {"TP53": 10.5, "BRCA1": 5.2},
            "S2": {"TP53": 8.1, "BRCA1": 4.9}
        }
    }

@pytest.fixture
def sample_model_data():
    """Generate valid sample data for model output schema."""
    return {
        "metadata": {
            "tumor_type": "BRCA",
            "model_type": "ElasticNet",
            "gene_panel_source": "results/meta_analysis/gene_panel.json",
            "training_date": "2023-10-02T10:00:00Z",
            "cv_folds": 5
        },
        "model_info": {
            "alpha": 0.1,
            "l1_ratio": 0.5,
            "final_alpha": 0.1,
            "final_l1_ratio": 0.5,
            "n_features": 50
        },
        "performance_metrics": {
            "auc_roc": 0.85,
            "auc_pr": 0.80,
            "accuracy": 0.82,
            "precision": 0.80,
            "recall": 0.75,
            "f1_score": 0.77
        },
        "coefficients": [
            {"gene_symbol": "TP53", "coefficient": 1.2},
            {"gene_symbol": "BRCA1", "coefficient": -0.5}
        ]
    }

@pytest.fixture
def sample_meta_data():
    """Generate valid sample data for meta-analysis schema."""
    return {
        "metadata": {
            "analysis_date": "2023-10-03T09:00:00Z",
            "method": "intersection",
            "tumor_types_included": ["BRCA", "LUAD", "COAD"],
            "selection_strategy": "Intersection of significant genes",
            "fallback_reason": None
        },
        "gene_panel": {
            "genes": ["TP53", "BRCA1", "EGFR"],
            "count": 3
        },
        "meta_analysis_results": [
            {
                "gene_symbol": "TP53",
                "combined_p_value": 0.001,
                "z_score": 3.5,
                "significant_in_count": 3,
                "tumor_type_pvalues": {"BRCA": 0.005, "LUAD": 0.002, "COAD": 0.001}
            }
        ]
    }

def test_schemas_exist():
    """Verify that all required schema files exist."""
    required_schemas = [
        "dataset.schema.yaml",
        "model_output.schema.yaml",
        "meta_analysis.schema.yaml"
    ]
    for schema in required_schemas:
        assert (CONTRACTS_DIR / schema).exists(), f"Missing schema: {schema}"

def test_schemas_load_valid_yaml():
    """Verify schemas are valid YAML."""
    for schema_file in ["dataset.schema.yaml", "model_output.schema.yaml", "meta_analysis.schema.yaml"]:
        try:
            schema = load_schema(schema_file)
            assert isinstance(schema, dict), f"Schema {schema_file} did not load as a dictionary"
        except Exception as e:
            pytest.fail(f"Failed to load {schema_file}: {e}")

def test_dataset_schema_structure(sample_dataset_data):
    """Validate sample data against the dataset schema."""
    schema = load_schema("dataset.schema.yaml")
    errors = validate_data_against_schema(sample_dataset_data, schema)
    assert not errors, f"Dataset validation failed: {errors}"

def test_model_output_schema_structure(sample_model_data):
    """Validate sample data against the model output schema."""
    schema = load_schema("model_output.schema.yaml")
    errors = validate_data_against_schema(sample_model_data, schema)
    assert not errors, f"Model output validation failed: {errors}"

def test_meta_analysis_schema_structure(sample_meta_data):
    """Validate sample data against the meta-analysis schema."""
    schema = load_schema("meta_analysis.schema.yaml")
    errors = validate_data_against_schema(sample_meta_data, schema)
    assert not errors, f"Meta-analysis validation failed: {errors}"

def test_sample_data_validation(sample_dataset_data):
    """Test that sample data actually passes validation."""
    schema = load_schema("dataset.schema.yaml")
    # Manually tweak data to ensure it's valid
    assert sample_dataset_data["metadata"]["sample_count"] == 100
    errors = validate_data_against_schema(sample_dataset_data, schema)
    assert len(errors) == 0

def test_invalid_data_catches_error():
    """Ensure validation catches missing required fields."""
    invalid_data = {
        "metadata": {}, # Missing required fields
        "samples": [],
        "features": []
    }
    schema = load_schema("dataset.schema.yaml")
    errors = validate_data_against_schema(invalid_data, schema)
    assert len(errors) > 0
    assert any("metadata" in e for e in errors)