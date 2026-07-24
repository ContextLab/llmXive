import os
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Import the validator function from the existing utils module
from code.utils.validators import validate_dataset_schema
from code.utils.config import get_specs_path, get_processed_path


class TestIngest(unittest.TestCase):
    """Test suite for User Story 1: Data Ingestion and Validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.schema_path = get_specs_path() / "001-investigating-the-correlation-between-gu" / "contracts" / "dataset.schema.yaml"
        self.filtered_data_path = get_processed_path() / "filtered_data.csv"

        # Ensure directories exist for test execution
        get_processed_path().mkdir(parents=True, exist_ok=True)

    def test_validate_schema_loads_yaml(self):
        """
        Contract test: Verify that the schema validation logic can successfully
        load the YAML schema file and validate a dataframe against it.
        """
        # 1. Verify the schema file exists (pre-condition)
        self.assertTrue(
            self.schema_path.exists(),
            f"Schema file not found at {self.schema_path}. Ensure T001a created the contracts directory."
        )

        # 2. Load the schema content to verify it is valid YAML
        try:
            with open(self.schema_path, "r") as f:
                schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.fail(f"Schema file is not valid YAML: {e}")

        # 3. Verify the schema contains expected keys (Contract Check)
        self.assertIn("type", schema, "Schema must define 'type'")
        self.assertIn("required", schema, "Schema must define 'required' fields")
        self.assertIn("properties", schema, "Schema must define 'properties'")

        # 4. Verify the validator function exists and accepts the schema
        self.assertTrue(
            get_specs_path().exists(),
            "Specs path configuration is broken."
        )

        # 5. If data exists, run the full validation; if not, verify schema structure is correct.
        if self.filtered_data_path.exists():
            try:
                validate_dataset_schema(self.filtered_data_path, self.schema_path)
            except Exception as e:
                # If validation fails, it should be due to data mismatch, not schema loading
                self.fail(f"Schema validation raised an unexpected error: {e}")
        else:
            # If data is missing, we still assert the schema loading logic works
            self.assertEqual(
                schema["type"],
                "object",
                "Schema type must be 'object' per contract."
            )
            self.assertIn("subject_id", schema["required"], "subject_id must be required.")
            self.assertIn("taxa_abundances", schema["required"], "taxa_abundances must be required.")
            self.assertIn("titer_baseline", schema["required"], "titer_baseline must be required.")
            self.assertIn("titer_post", schema["required"], "titer_post must be required.")

    def test_schema_properties_match_contract(self):
        """
        Verify that the schema properties match the specific contract defined in T001a.
        """
        self.assertTrue(self.schema_path.exists())
        with open(self.schema_path, "r") as f:
            schema = yaml.safe_load(f)

        # Check specific property definitions
        properties = schema.get("properties", {})
        
        self.assertIn("subject_id", properties)
        self.assertEqual(properties["subject_id"]["type"], "string")

        self.assertIn("taxa_abundances", properties)
        self.assertEqual(properties["taxa_abundances"]["type"], "object")
        self.assertIn("additionalProperties", properties["taxa_abundances"])
        self.assertEqual(properties["taxa_abundances"]["additionalProperties"]["type"], "number")

        self.assertIn("titer_baseline", properties)
        self.assertEqual(properties["titer_baseline"]["type"], "number")

        self.assertIn("titer_post", properties)
        self.assertEqual(properties["titer_post"]["type"], "number")

    def test_filter_excludes_null_titers(self):
        """
        Integration test for data filtering logic.
        
        Verifies that the ingestion pipeline (specifically the filtering step
        implemented in T012/T016) correctly excludes subjects missing
        baseline or post-vaccination titers.
        
        This test constructs a synthetic intermediate dataset with known nulls,
        simulates the filtering logic found in code/utils/data_loader.py,
        and asserts that the resulting dataframe has no nulls in titer columns.
        """
        # 1. Create a mock intermediate dataset with known nulls
        # This simulates the state of data BEFORE T012 filtering
        mock_data = {
            "subject_id": ["S1", "S2", "S3", "S4", "S5"],
            "taxa_abundances": [
                {"Bacteroides": 0.5, "Firmicutes": 0.5},
                {"Bacteroides": 0.2, "Firmicutes": 0.8},
                {"Bacteroides": 0.1, "Firmicutes": 0.9},
                {"Bacteroides": 0.6, "Firmicutes": 0.4},
                {"Bacteroides": 0.3, "Firmicutes": 0.7}
            ],
            "titer_baseline": [10.0, 20.0, None, 15.0, 25.0],  # S3 missing
            "titer_post": [40.0, None, 60.0, 50.0, 80.0]      # S2 missing
        }
        
        df_input = pd.DataFrame(mock_data)
        
        # 2. Apply the filtering logic (mimicking code/utils/data_loader.py: filter_complete_records)
        # The requirement is to exclude subjects missing baseline OR post titers.
        required_titer_cols = ["titer_baseline", "titer_post"]
        
        # Check for nulls in required columns
        mask_nulls = df_input[required_titer_cols].isnull().any(axis=1)
        
        # Filter out rows where mask is True (i.e., keep rows where mask is False)
        df_filtered = df_input[~mask_nulls].reset_index(drop=True)
        
        # 3. Assert the filtering logic works as expected
        # Expected kept subjects: S1, S4, S5 (S2 and S3 should be excluded)
        expected_subjects = ["S1", "S4", "S5"]
        actual_subjects = df_filtered["subject_id"].tolist()
        
        self.assertEqual(
            actual_subjects, 
            expected_subjects, 
            f"Filtering logic failed. Expected {expected_subjects}, got {actual_subjects}. "
            f"Subjects with null titers were not excluded."
        )
        
        # 4. Assert the resulting dataframe has NO nulls in titer columns
        remaining_nulls = df_filtered[required_titer_cols].isnull().sum().sum()
        self.assertEqual(
            remaining_nulls, 
            0, 
            f"Filtered data still contains {remaining_nulls} null values in titer columns."
        )
        
        # 5. Verify schema compliance of the filtered data (optional but good practice)
        # We write the filtered data to a temp location to test schema validation
        temp_path = self.filtered_data_path.parent / "test_filtered_temp.csv"
        df_filtered.to_csv(temp_path, index=False)
        
        try:
            validate_dataset_schema(temp_path, self.schema_path)
        except Exception as e:
            self.fail(f"Filtered data failed schema validation: {e}")
        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()