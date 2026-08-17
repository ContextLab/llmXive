import os
import unittest
import yaml
import pandas as pd
from pathlib import Path
from code.utils.validators import validate_dataset_schema


class TestIngest(unittest.TestCase):
    """Unit tests for User Story 1: Data Ingestion and Validation."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.schema_path = cls.project_root / "specs" / "001-investigating-the-correlation-between-gu" / "contracts" / "dataset.schema.yaml"
        cls.sample_data_path = cls.project_root / "data" / "processed" / "cleared_with_diversity.csv"

    def test_validate_schema_loads_yaml(self):
        """
        Contract test: Verify that the schema validation function can successfully
        load the YAML schema file and that the schema exists at the expected path.
        
        This ensures the schema definition is accessible and parsable before
        attempting to validate data against it.
        """
        # Verify schema file exists
        self.assertTrue(
            self.schema_path.exists(),
            f"Schema file not found at {self.schema_path}"
        )

        # Load the schema YAML to verify it's valid and readable
        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            
            # Verify essential schema keys exist
            self.assertIn('type', schema, "Schema must define 'type'")
            self.assertIn('required', schema, "Schema must define 'required' fields")
            self.assertIn('properties', schema, "Schema must define 'properties'")
            
            # Verify required fields match expectations
            required_fields = schema['required']
            self.assertIn('subject_id', required_fields, "subject_id must be required")
            self.assertIn('taxa_abundances', required_fields, "taxa_abundances must be required")
            self.assertIn('titer_baseline', required_fields, "titer_baseline must be required")
            self.assertIn('titer_post', required_fields, "titer_post must be required")
            
        except yaml.YAMLError as e:
            self.fail(f"Schema YAML is not valid: {e}")

    def test_filter_excludes_null_titers(self):
        """
        Integration test: Verify that the data filtering logic correctly excludes
        subjects with null or missing titer values.
        
        This test checks that the merged dataset in cleared_with_diversity.csv
        contains no null values in the required titer columns.
        
        It validates the logic implemented in T011d (Merge Microbiome and Serology),
        which explicitly filters out subjects where titer_baseline OR titer_post is null/missing.
        """
        if not self.sample_data_path.exists():
            self.skipTest(f"Sample data not found at {self.sample_data_path}. "
                        "Run the ingestion pipeline first (e.g., via code/main.py or code/01_merge_strategy_b.py).")

        # Load the processed dataset
        df = pd.read_csv(self.sample_data_path)

        # Verify required titer columns exist
        self.assertIn('titer_baseline', df.columns, "titer_baseline column missing")
        self.assertIn('titer_post', df.columns, "titer_post column missing")

        # Check for null/missing values in titer columns
        baseline_nulls = df['titer_baseline'].isnull().sum()
        post_nulls = df['titer_post'].isnull().sum()

        self.assertEqual(
            baseline_nulls, 0,
            f"Found {baseline_nulls} null values in titer_baseline column. Filtering logic failed to exclude nulls."
        )
        self.assertEqual(
            post_nulls, 0,
            f"Found {post_nulls} null values in titer_post column. Filtering logic failed to exclude nulls."
        )

    def test_schema_validation_against_data(self):
        """
        Contract test: Validate the actual processed data against the schema.
        """
        if not self.schema_path.exists():
            self.skipTest(f"Schema file not found at {self.schema_path}")

        if not self.sample_data_path.exists():
            self.skipTest(f"Sample data not found at {self.sample_data_path}")

        # Load schema
        with open(self.schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Load data
        df = pd.read_csv(self.sample_data_path)

        # Validate using the validator function
        is_valid = validate_dataset_schema(df, schema)
        
        self.assertTrue(
            is_valid,
            "Processed data failed schema validation"
        )

    def test_minimum_sample_size(self):
        """
        Integration test: Verify that the final dataset meets the minimum
        sample size requirement (N >= 50).
        """
        if not self.sample_data_path.exists():
            self.skipTest(f"Sample data not found at {self.sample_data_path}")

        df = pd.read_csv(self.sample_data_path)
        n_subjects = len(df)

        self.assertGreaterEqual(
            n_subjects, 50,
            f"Sample size ({n_subjects}) is below minimum requirement of 50"
        )


if __name__ == '__main__':
    unittest.main()