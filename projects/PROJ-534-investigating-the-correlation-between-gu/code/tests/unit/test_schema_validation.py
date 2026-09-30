import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if necessary
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.validation import load_schema, validate_dataframe_against_schema
from code.src.utils.config import get_raw_data_dir

class TestSchemaValidation:
    """
    Unit tests for validating the generated synthetic data against the dataset schema.
    Ensures strict type enforcement (int, float, bool, enum) as per T009.
    """

    @pytest.fixture
    def schema_path(self):
        """Returns the path to the dataset schema."""
        return Path("code/contracts/dataset.schema.yaml")

    @pytest.fixture
    def data_path(self):
        """Returns the path to the generated synthetic data."""
        return get_raw_data_dir() / "synthetic_data.csv"

    def test_schema_loads_correctly(self, schema_path):
        """Verify that the schema file can be loaded."""
        if not schema_path.exists():
            pytest.fail(f"Schema file not found at {schema_path}")
        schema = load_schema(schema_path)
        assert "fields" in schema or "entities" in schema, "Schema must contain field definitions"

    def test_data_file_exists(self, data_path):
        """Verify that the synthetic data file exists."""
        assert data_path.exists(), f"Synthetic data file not found at {data_path}"

    def test_types_enforced_int_float_bool_enum(self, schema_path, data_path):
        """
        Main test for T009: Validate strict type enforcement.
        Checks that:
        - 'age' is int
        - 'bmi', 'cognitive_flexibility_score', 'shannon_diversity' are float
        - 'antibiotic_use' is bool
        - 'sex' is enum (str)
        """
        schema = load_schema(schema_path)
        df = pd.read_csv(data_path)

        # Run the validation logic from the utility module
        # This function should raise an error if types don't match the schema
        try:
            validate_dataframe_against_schema(df, schema)
            # If we get here, validation passed
            assert True
        except ValueError as e:
            pytest.fail(f"Schema validation failed: {str(e)}")

    def test_specific_field_types(self, schema_path, data_path):
        """
        Specific checks for known fields defined in T003.
        """
        schema = load_schema(schema_path)
        df = pd.read_csv(data_path)

        # Check 'age' is integer-like
        assert df['age'].dtype in ['int64', 'int32', 'int16', 'int8', 'uint8', 'uint16', 'uint32', 'uint64'], \
            f"Field 'age' must be integer type, got {df['age'].dtype}"

        # Check 'bmi' is float-like
        assert np.issubdtype(df['bmi'].dtype, np.floating), \
            f"Field 'bmi' must be float type, got {df['bmi'].dtype}"

        # Check 'cognitive_flexibility_score' is float-like
        assert np.issubdtype(df['cognitive_flexibility_score'].dtype, np.floating), \
            f"Field 'cognitive_flexibility_score' must be float type, got {df['cognitive_flexibility_score'].dtype}"

        # Check 'antibiotic_use' is boolean
        assert df['antibiotic_use'].dtype == 'bool', \
            f"Field 'antibiotic_use' must be boolean type, got {df['antibiotic_use'].dtype}"

        # Check 'sex' is string/enum
        assert df['sex'].dtype == 'object', \
            f"Field 'sex' must be object (string) type for enum, got {df['sex'].dtype}"
        
        # Ensure 'sex' contains only expected values if defined in schema
        # Assuming 'M' and 'F' based on common practice, but schema should define this
        valid_sex_values = ['M', 'F', 'Other'] # Placeholder, actual validation happens in validate_dataframe_against_schema
        assert df['sex'].isin(valid_sex_values).all(), "Sex values must be within allowed enum"