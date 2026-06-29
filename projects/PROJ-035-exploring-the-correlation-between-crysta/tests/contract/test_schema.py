"""
Contract test for merged_perovskite.schema.yaml schema validation.

This test validates that the merged perovskite dataset conforms to the
schema defined in contracts/merged_perovskite.schema.yaml.

TDD Approach: This test is written to FAIL first, then implementation
follows (per task description requirements).
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import unittest
import pandas as pd
import yaml

# Project root path (tests/ is at repository root per path conventions)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "merged_perovskite.schema.yaml"


def load_schema() -> Dict[str, Any]:
    """Load and return the schema definition from YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found at {SCHEMA_PATH}. "
            "Run T005 to create the schema first."
        )
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def validate_column_types(df: pd.DataFrame, columns: Dict[str, str]) -> List[str]:
    """
    Validate that DataFrame columns match expected types.
    
    Args:
        df: DataFrame to validate
        columns: Dict mapping column names to expected types
                
    Returns:
        List of validation error messages (empty if all pass)
    """
    errors = []
    for col_name, expected_type in columns.items():
        if col_name not in df.columns:
            errors.append(f"Missing required column: {col_name}")
            continue
        
        # Map schema types to pandas dtypes
        type_mapping = {
            "string": "object",
            "integer": "int64",
            "number": "float64",
            "float": "float64",
            "boolean": "bool",
        }
        expected_dtype = type_mapping.get(expected_type, expected_type)
        
        # Check dtype compatibility
        actual_dtype = str(df[col_name].dtype)
        if expected_dtype not in actual_dtype:
            errors.append(
                f"Column '{col_name}' has dtype {actual_dtype}, "
                f"expected {expected_dtype}"
            )
    
    return errors


def validate_required_columns(df: pd.DataFrame, required: List[str]) -> List[str]:
    """
    Validate that all required columns exist in DataFrame.
    
    Args:
        df: DataFrame to validate
        required: List of required column names
                
    Returns:
        List of missing column names
    """
    return [col for col in required if col not in df.columns]


def validate_no_nulls(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """
    Validate that specified columns have no null values.
    
    Args:
        df: DataFrame to validate
        columns: List of columns that must not contain nulls
                
    Returns:
        List of columns with null values found
    """
    null_columns = []
    for col in columns:
        if col in df.columns and df[col].isnull().any():
            null_count = df[col].isnull().sum()
            null_columns.append(f"{col}: {null_count} null values")
    return null_columns


def validate_row_count(df: pd.DataFrame, min_rows: int = 50) -> Optional[str]:
    """
    Validate that DataFrame meets minimum row count (SC-001).
    
    Args:
        df: DataFrame to validate
        min_rows: Minimum required rows
                
    Returns:
        Error message if validation fails, None if passes
    """
    if len(df) < min_rows:
        return f"Insufficient samples: N={len(df)} < {min_rows} (SC-001)"
    return None


class TestMergedPerovskiteSchema(unittest.TestCase):
    """
    Contract tests for merged_perovskite.schema.yaml.
    
    These tests validate that the merged perovskite dataset conforms
    to the schema requirements defined in T005.
    """

    @classmethod
    def setUpClass(cls):
        """Load schema once for all tests."""
        try:
            cls.schema = load_schema()
        except FileNotFoundError as e:
            # Mark tests as skipped if schema doesn't exist yet
            cls.schema = None
            cls.skip_reason = str(e)

    def setUp(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()

    def test_schema_file_exists(self):
        """
        Test that the schema file exists at expected location.
        
        This test will FAIL if T005 has not been completed.
        """
        self.assertTrue(
            SCHEMA_PATH.exists(),
            f"Schema file not found at {SCHEMA_PATH}. "
            "Run T005 to create contracts/merged_perovskite.schema.yaml"
        )

    def test_schema_has_required_sections(self):
        """
        Test that schema contains required sections: title, description,
        properties, and required columns.
        
        This test validates the schema structure itself.
        """
        if self.schema is None:
            self.skipTest(self.skip_reason)
        
        self.assertIn("title", self.schema, "Schema missing 'title'")
        self.assertIn("description", self.schema, "Schema missing 'description'")
        self.assertIn("properties", self.schema, "Schema missing 'properties'")
        
        # Check for required columns definition
        self.assertIn("required_columns", self.schema,
                    "Schema missing 'required_columns'")

    def test_schema_properties_defined(self):
        """
        Test that all expected properties are defined in schema.
        
        Expected properties based on perovskite data model:
        - structure_id: unique identifier
        - formula: chemical formula
        - thermal_conductivity: W/(m·K)
        - temperature: measurement temperature in Kelvin
        - source_reference: peer-reviewed literature citation
        """
        if self.schema is None:
            self.skipTest(self.skip_reason)
        
        properties = self.schema.get("properties", {})
        expected_properties = [
            "structure_id",
            "formula",
            "thermal_conductivity",
            "temperature",
            "source_reference",
        ]
        
        for prop in expected_properties:
            self.assertIn(
                prop, properties,
                f"Schema missing expected property: {prop}"
            )

    def test_schema_required_columns_specified(self):
        """
        Test that schema specifies which columns are required.
        
        Required columns should include at least:
        - structure_id
        - thermal_conductivity
        """
        if self.schema is None:
            self.skipTest(self.skip_reason)
        
        required_columns = self.schema.get("required_columns", [])
        self.assertIn(
            "structure_id", required_columns,
            "Schema should require 'structure_id' column"
        )
        self.assertIn(
            "thermal_conductivity", required_columns,
            "Schema should require 'thermal_conductivity' column"
        )

    def test_validate_column_types(self):
        """
        Test the column type validation function.
        
        This tests the helper function that will be used to validate
        actual data against schema type definitions.
        """
        # Create test DataFrame with known types
        test_df = pd.DataFrame({
            "structure_id": ["mp-123", "mp-456"],
            "thermal_conductivity": [10.5, 15.2],
            "temperature": [300.0, 300.0],
        })
        
        # Define expected types from schema
        columns = {
            "structure_id": "string",
            "thermal_conductivity": "float",
            "temperature": "float",
        }
        
        errors = validate_column_types(test_df, columns)
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

    def test_validate_required_columns(self):
        """
        Test the required column validation function.
        """
        test_df = pd.DataFrame({
            "structure_id": ["mp-123"],
            "thermal_conductivity": [10.5],
        })
        
        required = ["structure_id", "thermal_conductivity", "formula"]
        missing = validate_required_columns(test_df, required)
        
        self.assertIn("formula", missing, "Should detect missing 'formula' column")
        self.assertNotIn("structure_id", missing, "Should not report existing column as missing")

    def test_validate_no_nulls(self):
        """
        Test the null value validation function.
        """
        test_df = pd.DataFrame({
            "structure_id": ["mp-123", None],
            "thermal_conductivity": [10.5, 15.2],
        })
        
        columns = ["structure_id", "thermal_conductivity"]
        null_cols = validate_no_nulls(test_df, columns)
        
        self.assertEqual(len(null_cols), 1, "Should detect one column with nulls")
        self.assertIn("structure_id", null_cols[0], "Should identify structure_id as having nulls")

    def test_validate_row_count(self):
        """
        Test the minimum row count validation (SC-001).
        """
        # Test with sufficient rows
        sufficient_df = pd.DataFrame({
            "structure_id": [f"mp-{i}" for i in range(50)],
            "thermal_conductivity": [10.0] * 50,
        })
        error = validate_row_count(sufficient_df, min_rows=50)
        self.assertIsNone(error, "Should pass with exactly 50 rows")
        
        # Test with insufficient rows
        insufficient_df = pd.DataFrame({
            "structure_id": [f"mp-{i}" for i in range(25)],
            "thermal_conductivity": [10.0] * 25,
        })
        error = validate_row_count(insufficient_df, min_rows=50)
        self.assertIsNotNone(error, "Should fail with less than 50 rows")
        self.assertIn("Insufficient samples", error, "Error message should mention insufficient samples")

    def test_full_schema_validation(self):
        """
        Integration test: Validate a complete sample dataset against schema.
        
        This test creates a sample dataset that should pass all schema
        validations and verifies the full validation pipeline works.
        """
        if self.schema is None:
            self.skipTest(self.skip_reason)
        
        # Create sample dataset that should pass validation
        sample_data = {
            "structure_id": [f"mp-{i:04d}" for i in range(55)],
            "formula": ["ABX3"] * 55,
            "thermal_conductivity": [10.0 + (i * 0.1) for i in range(55)],
            "temperature": [300.0] * 55,
            "source_reference": ["Smith et al. 2021"] * 55,
        }
        test_df = pd.DataFrame(sample_data)
        
        # Validate against schema requirements
        properties = self.schema.get("properties", {})
        required_columns = self.schema.get("required_columns", [])
        no_null_columns = self.schema.get("no_null_columns", required_columns)
        
        # Check required columns
        missing_cols = validate_required_columns(test_df, required_columns)
        self.assertEqual(len(missing_cols), 0, f"Missing columns: {missing_cols}")
        
        # Check no nulls in required columns
        null_issues = validate_no_nulls(test_df, no_null_columns)
        self.assertEqual(len(null_issues), 0, f"Null values found: {null_issues}")
        
        # Check row count
        row_error = validate_row_count(test_df, min_rows=50)
        self.assertIsNone(row_error, f"Row count validation failed: {row_error}")

    def test_schema_conforms_to_spec(self):
        """
        Test that schema matches spec.md requirements for US1.
        
        Per spec.md US1 requirements:
        - Must include structure_id for Materials Project references
        - Must include thermal_conductivity from literature/NIST (not MP)
        - Must include source_reference for peer-reviewed citations
        """
        if self.schema is None:
            self.skipTest(self.skip_reason)
        
        properties = self.schema.get("properties", {})
        
        # Verify structure_id is defined with proper constraints
        self.assertIn("structure_id", properties)
        self.assertEqual(
            properties["structure_id"].get("type"), "string",
            "structure_id should be string type"
        )
        
        # Verify thermal_conductivity is defined
        self.assertIn("thermal_conductivity", properties)
        self.assertIn(
            properties["thermal_conductivity"].get("type"),
            ["number", "float"],
            "thermal_conductivity should be numeric type"
        )
        
        # Verify source_reference is defined (FR-010: peer-reviewed/NIST source)
        self.assertIn("source_reference", properties)
        self.assertEqual(
            properties["source_reference"].get("type"), "string",
            "source_reference should be string type"
        )


def main():
    """Run tests via command line."""
    unittest.main()


if __name__ == "__main__":
    main()
