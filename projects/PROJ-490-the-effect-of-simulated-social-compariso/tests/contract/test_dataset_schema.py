import pytest
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.validators import load_schema, validate_dataframe_schema

def test_dataset_schema_validation():
    """
    Contract test for dataset schema validation.
    Verifies that the dataset schema (dataset.schema.yaml) correctly validates
    the structure of the input data (real or synthetic).
    """
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")
    
    schema = load_schema(schema_path)
    
    # Create a valid dummy dataframe
    df_valid = pd.DataFrame({
        'avatar_condition': [0, 1],
        'pre_self_esteem': [30.0, 40.0],
        'post_self_esteem': [32.0, 42.0],
        'comparison_tendency': [0.5, 0.8]
    })
    
    is_valid, errors = validate_dataframe_schema(df_valid, schema)
    assert is_valid, f"Valid dataframe failed schema validation: {errors}"
    
    # Create an invalid dataframe (missing column)
    df_invalid = pd.DataFrame({
        'avatar_condition': [0, 1],
        'pre_self_esteem': [30.0, 40.0]
        # Missing post_self_esteem and comparison_tendency
    })
    
    is_valid, errors = validate_dataframe_schema(df_invalid, schema)
    assert not is_valid, "Invalid dataframe should fail schema validation"
    assert 'comparison_tendency' in str(errors) or 'post_self_esteem' in str(errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])