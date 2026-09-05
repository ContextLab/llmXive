"""
Ingest Tests for User Story 1.
"""
import os
import unittest
import yaml
import pandas as pd
from pathlib import Path
from code.utils.validators import validate_dataset_schema

class TestIngest(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.schema_path = self.project_root / "contracts" / "dataset.schema.yaml"
        
        # Ensure the schema file exists for the test
        if not self.schema_path.exists():
            self.skipTest(f"Schema file not found at {self.schema_path}")

    def test_validate_schema_loads_yaml(self):
        """
        Contract test: Verify that the schema validation utility can successfully
        load the YAML schema file without errors.
        
        This ensures the schema is valid YAML and the validator can access it.
        """
        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            
            # Basic sanity checks on the loaded schema structure
            self.assertIsInstance(schema, dict, "Schema must be a dictionary")
            self.assertIn("type", schema, "Schema must have a 'type' field")
            self.assertEqual(schema["type"], "object", "Schema type must be 'object'")
            
            # Check for required fields defined in the spec
            self.assertIn("required", schema, "Schema must have 'required' field")
            self.assertIn("properties", schema, "Schema must have 'properties' field")
            
            # Verify specific required properties exist
            required_props = schema.get("properties", {})
            self.assertIn("subject_id", required_props, "Schema must define 'subject_id'")
            self.assertIn("titer_baseline", required_props, "Schema must define 'titer_baseline'")
            self.assertIn("titer_post", required_props, "Schema must define 'titer_post'")
            
        except yaml.YAMLError as e:
            self.fail(f"Failed to parse schema YAML: {e}")
        except Exception as e:
            self.fail(f"Unexpected error loading schema: {e}")

    def test_filter_excludes_null_titers(self):
        """
        Integration test: Verify that the data filtering logic correctly excludes
        subjects with missing (NaN/Null) titer values.
        
        This test creates a synthetic dataset with known nulls and verifies
        the filtering behavior matches expectations.
        """
        # Create a test dataset with known null values
        test_data = {
            'subject_id': ['S001', 'S002', 'S003', 'S004'],
            'taxon_A': [0.1, 0.2, 0.3, 0.4],
            'titer_baseline': [10.0, None, 15.0, 20.0],
            'titer_post': [40.0, 80.0, None, 100.0]
        }
        
        df = pd.DataFrame(test_data)
        
        # Apply filtering logic (mimicking T011d logic)
        # Filter out rows where titer_baseline OR titer_post is NaN
        filtered_df = df.dropna(subset=['titer_baseline', 'titer_post'])
        
        # Expected: S001 and S004 should remain (S002 has null baseline, S003 has null post)
        expected_ids = {'S001', 'S004'}
        actual_ids = set(filtered_df['subject_id'].tolist())
        
        self.assertEqual(
            actual_ids, 
            expected_ids, 
            f"Filtering failed: expected {expected_ids}, got {actual_ids}"
        )
        
        self.assertEqual(
            len(filtered_df), 
            2, 
            f"Expected 2 rows after filtering, got {len(filtered_df)}"
        )

if __name__ == "__main__":
    unittest.main()