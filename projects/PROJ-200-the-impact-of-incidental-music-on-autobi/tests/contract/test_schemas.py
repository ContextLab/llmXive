import pytest
import yaml
import jsonschema
from pathlib import Path
from llmxive_toolkit import paths

def test_dataset_schema_validity():
    """Verify that dataset.schema.yaml is a valid JSON schema."""
    schema_path = paths.root / "contracts" / "dataset.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # This will raise a SchemaError if the schema itself is invalid
    jsonschema.Draft7Validator.check_schema(schema)

def test_output_schema_validity():
    """Verify that output.schema.yaml is a valid JSON schema."""
    schema_path = paths.root / "contracts" / "output.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    jsonschema.Draft7Validator.check_schema(schema)

def test_aggregated_metric_instance():
    """Verify a sample AggregatedMetric matches the schema."""
    schema_path = paths.root / "contracts" / "dataset.schema.yaml"
    with open(schema_path, "r") as f:
        full_schema = yaml.safe_load(f)
    
    schema = full_schema["definitions"]["AggregatedMetric"]
    
    valid_instance = {
        "user_id": "user_123",
        "track_id": "track_456",
        "mean_vividness": 4.2,
        "mean_valence": 0.5,
        "count_cues": 3,
        "adolescent_exposure_ratio": 0.75
    }
    
    jsonschema.validate(instance=valid_instance, schema=schema)

def test_regression_results_instance():
    """Verify a sample RegressionResults matches the schema."""
    schema_path = paths.root / "contracts" / "output.schema.yaml"
    with open(schema_path, "r") as f:
        full_schema = yaml.safe_load(f)
    
    schema = full_schema["definitions"]["RegressionResults"]
    
    valid_instance = {
        "model_name": "LMM_v1",
        "coefficient_adolescent_exposure": 0.15,
        "se_adolescent_exposure": 0.04,
        "pvalue_adolescent_exposure": 0.001,
        "coefficient_popularity": -0.02,
        "pvalue_popularity": 0.45,
        "r_squared": 0.12,
        "vif_adolescent_exposure": 1.2,
        "vif_popularity": 1.1
    }
    
    jsonschema.validate(instance=valid_instance, schema=schema)