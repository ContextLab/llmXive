import yaml
import pytest
from llmxive_toolkit import paths

def test_per_sample_schema_columns():
    """
    Verify that the per_sample_errors schema contains exactly the required columns
    in the correct order.
    """
    # Resolve path relative to project root to avoid environment-specific failures
    schema_path = paths.root / "specs" / "001-assessing-uncertainty-quantification-tec" / "contracts" / "per_sample_errors.schema.yaml"
    
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    # Extract column names from the schema
    actual_columns = [col["name"] for col in schema.get("columns", [])]
    
    expected_columns = [
        "sample_id", 
        "dataset", 
        "method", 
        "prediction", 
        "lower_bound", 
        "upper_bound", 
        "ground_truth", 
        "abs_error"
    ]
    
    assert actual_columns == expected_columns, (
        f"Schema column mismatch.\nExpected: {expected_columns}\nActual: {actual_columns}"
    )