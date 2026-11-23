import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure we can import from the project
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from code.src.utils.validation import load_schema, validate_dataframe_against_schema
from code.src.utils.config import get_raw_data_dir, get_project_root

class TestSchemaValidation:
    """
    Contract test: Validates the generated synthetic data against the schema.
    This ensures strict type enforcement (int, float, bool, enum) as required by T009.
    """

    def test_schema_file_exists(self):
        project_root = get_project_root()
        schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"
        assert schema_path.exists(), "Schema file must exist"

    def test_data_file_exists(self):
        data_dir = get_raw_data_dir()
        data_path = data_dir / "synthetic_data.csv"
        assert data_path.exists(), "Synthetic data file must exist"

    def test_validate_synthetic_data_against_schema(self):
        """
        Main contract test: Load the synthetic data and validate it against the schema.
        This verifies that T008 (data generation) correctly adhered to T003 (schema definition).
        """
        project_root = get_project_root()
        schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"
        data_dir = get_raw_data_dir()
        data_path = data_dir / "synthetic_data.csv"

        # Load schema
        schema = load_schema(schema_path)
        
        # Load data
        df = pd.read_csv(data_path)

        # Validate
        is_valid, errors = validate_dataframe_against_schema(df, schema)

        # Assert
        assert is_valid, f"Data validation failed. Errors: {errors}"

    def test_field_types_enforcement(self):
        """
        Specific test for type enforcement: int, float, bool, enum.
        Checks a few critical fields to ensure types are correct.
        """
        project_root = get_project_root()
        schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"
        data_dir = get_raw_data_dir()
        data_path = data_dir / "synthetic_data.csv"

        schema = load_schema(schema_path)
        df = pd.read_csv(data_path)

        # Check 'age' is integer-like
        assert pd.api.types.is_integer_dtype(df['age']) or df['age'].apply(lambda x: float(x).is_integer()).all(), "age must be integer"

        # Check 'sex' is string (enum)
        assert df['sex'].dtype == 'object' or df['sex'].dtype.name == 'category', "sex must be object or category"
        valid_sex = schema['properties']['sex']['enum']
        assert df['sex'].isin(valid_sex).all(), f"sex values must be in {valid_sex}"

        # Check 'cognitive_flexibility_score' is float
        assert pd.api.types.is_float_dtype(df['cognitive_flexibility_score']), "cognitive_flexibility_score must be float"

        # Check 'antibiotic_use' is boolean
        assert df['antibiotic_use'].dtype == 'bool', "antibiotic_use must be boolean"