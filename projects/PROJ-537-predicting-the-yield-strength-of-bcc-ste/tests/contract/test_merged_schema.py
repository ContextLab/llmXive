"""
Contract test for merged dataset schema (User Story 1).

Validates that data/intermediate/merged.csv conforms to the schema defined
in contracts/dataset.schema.yaml.

Checks:
1. File existence
2. Required columns presence
3. Data types (basic)
4. Non-null constraints for critical fields
5. Row count >= 20 (MVP requirement)
"""

import os
import sys
import json
import yaml
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import CONFIG


def load_schema():
    """Load the dataset schema from contracts directory."""
    schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def load_merged_dataset():
    """Load the merged dataset from the expected location."""
    # The path should match what merge_and_filter.py writes
    data_path = PROJECT_ROOT / CONFIG.INTERMEDIATE_DATA_DIR / "merged.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at: {data_path}")
    
    return pd.read_csv(data_path)


class TestMergedDatasetSchema:
    """Contract tests for the merged dataset schema."""
    
    @pytest.fixture(scope="class")
    def schema(self):
        """Load the schema once for the test class."""
        return load_schema()
    
    @pytest.fixture(scope="class")
    def dataset(self):
        """Load the dataset once for the test class."""
        return load_merged_dataset()
    
    def test_file_exists(self, dataset):
        """Test that the merged dataset file exists."""
        assert dataset is not None, "Dataset could not be loaded"
    
    def test_required_columns_present(self, dataset, schema):
        """Test that all required columns from schema are present."""
        required_columns = schema.get("required_columns", [])
        actual_columns = set(dataset.columns)
        
        missing_columns = set(required_columns) - actual_columns
        
        assert len(missing_columns) == 0, (
            f"Missing required columns: {missing_columns}. "
            f"Found: {list(actual_columns)}"
        )
    
    def test_no_null_yield_strength(self, dataset):
        """Test that yield_strength_MPa has no null values."""
        null_count = dataset["yield_strength_MPa"].isnull().sum()
        assert null_count == 0, f"Found {null_count} null values in yield_strength_MPa"
    
    def test_no_null_shear_modulus(self, dataset):
        """Test that shear_modulus_GPa has no null values."""
        null_count = dataset["shear_modulus_GPa"].isnull().sum()
        assert null_count == 0, f"Found {null_count} null values in shear_modulus_GPa"
    
    def test_positive_yield_strength(self, dataset):
        """Test that yield_strength_MPa values are positive."""
        negative_count = (dataset["yield_strength_MPa"] <= 0).sum()
        assert negative_count == 0, (
            f"Found {negative_count} non-positive yield_strength_MPa values"
        )
    
    def test_positive_shear_modulus(self, dataset):
        """Test that shear_modulus_GPa values are positive."""
        negative_count = (dataset["shear_modulus_GPa"] <= 0).sum()
        assert negative_count == 0, (
            f"Found {negative_count} non-positive shear_modulus_GPa values"
        )
    
    def test_minimum_row_count(self, dataset):
        """Test that dataset has at least 20 rows (MVP requirement)."""
        min_rows = 20
        actual_rows = len(dataset)
        assert actual_rows >= min_rows, (
            f"Dataset has only {actual_rows} rows, "
            f"minimum required is {min_rows}. "
            f"System should halt with ERR_INSUFFICIENT_DATA."
        )
    
    def test_composition_columns_format(self, dataset, schema):
        """Test that composition columns contain valid numeric fractions."""
        composition_cols = [
            col for col in dataset.columns 
            if col.startswith("fraction_") or col.endswith("_fraction")
        ]
        
        if composition_cols:
            for col in composition_cols:
                # Check for non-negative values (fractions should be >= 0)
                negative_count = (dataset[col] < 0).sum()
                assert negative_count == 0, (
                    f"Found {negative_count} negative values in {col}"
                )
                
                # Check for values <= 1 (fractions should be <= 1)
                # Note: We allow small floating point errors
                invalid_count = (dataset[col] > 1.01).sum()
                assert invalid_count == 0, (
                    f"Found {invalid_count} values > 1.0 in {col}"
                )
    
    def test_data_types(self, dataset, schema):
        """Test basic data types for key columns."""
        # yield_strength_MPa should be numeric
        assert pd.api.types.is_numeric_dtype(
            dataset["yield_strength_MPa"]
        ), "yield_strength_MPa is not numeric"
        
        # shear_modulus_GPa should be numeric
        assert pd.api.types.is_numeric_dtype(
            dataset["shear_modulus_GPa"]
        ), "shear_modulus_GPa is not numeric"
    
    def test_bcc_filter_applied(self, dataset):
        """Test that all rows are BCC (Space Group 229)."""
        # If space_group column exists, verify all are 229
        if "space_group" in dataset.columns:
            non_bcc_count = (dataset["space_group"] != 229).sum()
            assert non_bcc_count == 0, (
                f"Found {non_bcc_count} rows with non-BCC space groups. "
                "All rows should be Space Group 229."
            )
        elif "structure_type" in dataset.columns:
            non_bcc_count = (dataset["structure_type"] != "bcc").sum()
            assert non_bcc_count == 0, (
                f"Found {non_bcc_count} rows with non-BCC structure types."
            )
    
    def test_schema_conformity(self, dataset, schema):
        """
        Comprehensive schema conformity check.
        
        Validates that the dataset matches the schema definition
        including column types and constraints.
        """
        errors = []
        
        # Check column definitions
        columns_def = schema.get("columns", {})
        for col_name, col_spec in columns_def.items():
            if col_name in dataset.columns:
                # Check if nullable constraint is respected
                if not col_spec.get("nullable", True):
                    null_count = dataset[col_name].isnull().sum()
                    if null_count > 0:
                        errors.append(
                            f"Column {col_name} marked as NOT NULL but has {null_count} nulls"
                        )
                
                # Check data type if specified
                if "dtype" in col_spec:
                    expected_type = col_spec["dtype"]
                    actual_type = str(dataset[col_name].dtype)
                    
                    # Simple type mapping
                    type_map = {
                        "float": ["float32", "float64"],
                        "int": ["int32", "int64"],
                        "string": ["object", "string"],
                    }
                    
                    if expected_type in type_map:
                        if actual_type not in type_map[expected_type]:
                            errors.append(
                                f"Column {col_name}: expected {expected_type}, got {actual_type}"
                            )
        
        if errors:
            pytest.fail("Schema conformity errors:\n" + "\n".join(errors))

if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])