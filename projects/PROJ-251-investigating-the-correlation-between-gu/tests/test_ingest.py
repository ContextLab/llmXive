import os
import unittest
import yaml
import pandas as pd
from pathlib import Path
from code.utils.validators import validate_dataset_schema

class TestIngest(unittest.TestCase):
    def test_validate_schema_loads_yaml(self):
        """Test that the schema loader correctly reads the YAML file."""
        schema_path = Path(__file__).parent.parent.parent / "specs" / "001-investigating-the-correlation-between-gu" / "contracts" / "dataset.schema.yaml"
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            self.assertIn('properties', schema)
            self.assertIn('subject_id', schema['properties'])
        else:
            self.skipTest("Schema file not found")

    def test_filter_excludes_null_titers(self):
        """Test that rows with null titers are excluded."""
        # Create a mock dataframe
        data = {
            'subject_id': ['A', 'B', 'C'],
            'titer_baseline': [10.0, None, 20.0],
            'titer_post': [40.0, 50.0, None]
        }
        df = pd.DataFrame(data)
        
        # Filter logic (mimicking T011d)
        filtered = df.dropna(subset=['titer_baseline', 'titer_post'])
        
        self.assertEqual(len(filtered), 0)
        # In a real scenario, we'd expect 0 if all have NaN in one of the columns
        # Let's adjust data to have one valid
        data = {
            'subject_id': ['A', 'B', 'C'],
            'titer_baseline': [10.0, None, 20.0],
            'titer_post': [40.0, 50.0, 80.0]
        }
        df = pd.DataFrame(data)
        filtered = df.dropna(subset=['titer_baseline', 'titer_post'])
        self.assertEqual(len(filtered), 2)
        self.assertNotIn('B', filtered['subject_id'].values)