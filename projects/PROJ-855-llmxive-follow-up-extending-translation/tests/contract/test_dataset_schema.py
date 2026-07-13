import json
import os
import pytest
from pathlib import Path

# Import real utilities from the project
from utils.data_utils import load_schema, validate_against_schema

# Determine the project root (parent of 'code' and 'tests')
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-gene-regulation" / "contracts"
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Path to the generated dataset (expected output of T011/T016)
DATASET_PATH = DATA_DIR / "synthetic_episodes.parquet"
SCHEMA_PATH = SCHEMAS_DIR / "dataset.schema.yaml"


class TestDatasetSchema:
    """
    Contract test for the synthetic dataset schema.
    
    This test verifies that the generated dataset (synthetic_episodes.parquet)
    strictly adheres to the schema defined in specs/001-gene-regulation/contracts/dataset.schema.yaml.
    
    It ensures:
    1. The file exists.
    2. The schema file exists.
    3. The data columns match the schema definition.
    4. No forbidden columns (rotation, force, torque) are present (enforcing FR-001).
    """

    def test_schema_file_exists(self):
        """Assert that the schema definition file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_dataset_file_exists(self):
        """Assert that the generated dataset file exists."""
        assert DATASET_PATH.exists(), (
            f"Dataset file not found at {DATASET_PATH}. "
            "Run code/generate_data.py (Task T011/T016) first."
        )

    def test_dataset_conforms_to_schema(self):
        """
        Validate the dataset against the YAML schema.
        
        This uses the load_schema and validate_against_schema utilities
        from utils.data_utils to perform the check.
        """
        # Load the schema
        schema = load_schema(SCHEMA_PATH)
        
        # Load the dataset (using pandas/parquet as implied by the task)
        import pandas as pd
        df = pd.read_parquet(DATASET_PATH)

        # Perform validation
        # validate_against_schema returns (is_valid, error_message)
        is_valid, error_msg = validate_against_schema(df, schema)

        assert is_valid, (
            f"Dataset failed schema validation:\n{error_msg}\n"
            f"Dataset columns: {list(df.columns)}\n"
            f"Schema requirements: {schema.get('required_columns', [])}"
        )

    def test_no_forbidden_columns(self):
        """
        Explicitly check for forbidden columns (rotation, force, torque).
        
        This is a defensive check to ensure FR-001 is met, even if the
        schema validation passes for other reasons.
        """
        import pandas as pd
        df = pd.read_parquet(DATASET_PATH)
        
        forbidden_keywords = ['rotation', 'force', 'torque', 'quaternion', 'angular']
        found_forbidden = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in forbidden_keywords):
                found_forbidden.append(col)
        
        assert len(found_forbidden) == 0, (
            f"Dataset contains forbidden columns violating FR-001: {found_forbidden}. "
            "Rotation, force, and torque data must be excluded."
        )

    def test_required_columns_present(self):
        """
        Ensure all required columns from the schema are present.
        """
        import pandas as pd
        df = pd.read_parquet(DATASET_PATH)
        schema = load_schema(SCHEMA_PATH)
        
        required_cols = schema.get('required_columns', [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        assert len(missing_cols) == 0, (
            f"Dataset is missing required columns: {missing_cols}. "
            f"Expected: {required_cols}"
        )

    def test_column_types_match_schema(self):
        """
        Verify that the data types of columns match the schema definition.
        """
        import pandas as pd
        import numpy as np
        df = pd.read_parquet(DATASET_PATH)
        schema = load_schema(SCHEMA_PATH)
        
        column_specs = schema.get('columns', {})
        
        for col_name, spec in column_specs.items():
            if col_name not in df.columns:
                continue  # Already covered by required_columns test
            
            expected_type = spec.get('type')
            actual_dtype = df[col_name].dtype
            
            # Map common schema types to numpy/pandas dtypes
            type_map = {
                'float': ['float32', 'float64'],
                'integer': ['int32', 'int64'],
                'boolean': ['bool'],
                'string': ['object', 'string']
            }
            
            expected_dtypes = type_map.get(expected_type, [])
            if expected_dtypes and str(actual_dtype) not in expected_dtypes:
                # Allow some flexibility for int/float in numerical columns
                if expected_type == 'float' and str(actual_dtype).startswith('int'):
                    continue 
                
                pytest.fail(
                    f"Column '{col_name}' has dtype '{actual_dtype}', "
                    f"but schema expects '{expected_type}' ({expected_dtypes})"
                )
