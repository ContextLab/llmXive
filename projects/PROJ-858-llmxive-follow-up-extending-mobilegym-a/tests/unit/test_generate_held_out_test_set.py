import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from typing import Dict, Any, Set

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scheduler.generate_held_out_test_set import (
    extract_training_variables,
    extract_schema_variables,
    generate_held_out_set,
    load_json_file
)

class TestHeldOutTestSetGeneration(TestCase):
    """
    Unit tests for the held-out test set generation logic (T029).
    
    These tests verify FR-005: The held-out test set contains state variables
    NOT present in the training-time State Coverage Vector.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create sample training coverage data
        self.training_data = {
            "vectors": [
                {
                    "id": "rollout_1",
                    "variables": ["dark_mode", "unread_count", "battery_level"],
                    "coverage": {"dark_mode": 1, "unread_count": 1, "battery_level": 0}
                },
                {
                    "id": "rollout_2",
                    "variables": ["dark_mode", "network_status", "app_version"],
                    "coverage": {"dark_mode": 1, "network_status": 0, "app_version": 1}
                }
            ]
        }
        
        self.training_file = os.path.join(self.test_dir, "training_vectors.json")
        with open(self.training_file, 'w') as f:
            json.dump(self.training_data, f)
        
        # Create sample schema data
        self.schema_data = {
            "properties": {
                "dark_mode": {"type": "boolean"},
                "unread_count": {"type": "integer"},
                "battery_level": {"type": "integer"},
                "network_status": {"type": "string"},
                "app_version": {"type": "string"},
                "location_permission": {"type": "boolean"},
                "notification_enabled": {"type": "boolean"},
                "camera_access": {"type": "boolean"}
            }
        }
        
        self.schema_file = os.path.join(self.test_dir, "schema.json")
        with open(self.schema_file, 'w') as f:
            json.dump(self.schema_data, f)
        
        self.output_file = os.path.join(self.test_dir, "held_out_test_set.json")

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_extract_training_variables(self):
        """Test that training variables are correctly extracted from coverage vectors."""
        training_vars = extract_training_variables(self.training_file)
        
        expected_vars = {"dark_mode", "unread_count", "battery_level", "network_status", "app_version"}
        self.assertEqual(training_vars, expected_vars)
        self.assertEqual(len(training_vars), 5)

    def test_extract_schema_variables(self):
        """Test that schema variables are correctly extracted."""
        schema_vars = extract_schema_variables(self.schema_file)
        
        expected_vars = {
            "dark_mode", "unread_count", "battery_level", 
            "network_status", "app_version", "location_permission",
            "notification_enabled", "camera_access"
        }
        self.assertEqual(schema_vars, expected_vars)
        self.assertEqual(len(schema_vars), 8)

    def test_held_out_computation(self):
        """Test that held-out variables are correctly computed (schema - training)."""
        training_vars = {"dark_mode", "unread_count", "battery_level", "network_status", "app_version"}
        schema_vars = {
            "dark_mode", "unread_count", "battery_level", 
            "network_status", "app_version", "location_permission",
            "notification_enabled", "camera_access"
        }
        
        held_out = generate_held_out_set(
            training_vars=training_vars,
            schema_vars=schema_vars,
            output_path=self.output_file
        )
        
        # Verify the computation
        expected_held_out = {"location_permission", "notification_enabled", "camera_access"}
        self.assertEqual(set(held_out['held_out_variables']), expected_held_out)
        self.assertEqual(len(held_out['held_out_variables']), 3)
        
        # Verify metadata
        self.assertEqual(held_out['metadata']['total_schema_variables'], 8)
        self.assertEqual(held_out['metadata']['training_variables_count'], 5)
        self.assertEqual(held_out['metadata']['held_out_variables_count'], 3)
        
        # Verify file was written
        self.assertTrue(os.path.exists(self.output_file))
        
        with open(self.output_file, 'r') as f:
            written_data = json.load(f)
        
        self.assertEqual(written_data, held_out)

    def test_no_held_out_variables(self):
        """Test behavior when all schema variables are in training set."""
        training_vars = {"var1", "var2", "var3"}
        schema_vars = {"var1", "var2", "var3"}
        
        output_file = os.path.join(self.test_dir, "empty_held_out.json")
        held_out = generate_held_out_set(
            training_vars=training_vars,
            schema_vars=schema_vars,
            output_path=output_file
        )
        
        self.assertEqual(len(held_out['held_out_variables']), 0)
        self.assertEqual(held_out['metadata']['held_out_variables_count'], 0)
        self.assertEqual(held_out['metadata']['coverage_ratio'], 1.0)

    def test_held_out_structure(self):
        """Test that the held-out test set has the correct structure for FR-005."""
        training_vars = {"dark_mode"}
        schema_vars = {"dark_mode", "network_status", "battery_level"}
        
        held_out = generate_held_out_set(
            training_vars=training_vars,
            schema_vars=schema_vars,
            output_path=self.output_file
        )
        
        # Check required keys
        self.assertIn('metadata', held_out)
        self.assertIn('training_variables', held_out)
        self.assertIn('held_out_variables', held_out)
        self.assertIn('schema_variables', held_out)
        self.assertIn('description', held_out)
        
        # Check metadata keys
        self.assertIn('generated_at', held_out['metadata'])
        self.assertIn('purpose', held_out['metadata'])
        self.assertIn('total_schema_variables', held_out['metadata'])
        self.assertIn('training_variables_count', held_out['metadata'])
        self.assertIn('held_out_variables_count', held_out['metadata'])
        
        # Verify FR-005 purpose
        self.assertIn('FR-005', held_out['metadata']['purpose'])
        self.assertIn('NOT present', held_out['metadata']['purpose'])

    def test_disjoint_sets(self):
        """Verify that held-out variables and training variables are disjoint."""
        training_vars = {"a", "b", "c"}
        schema_vars = {"a", "b", "c", "d", "e"}
        
        held_out = generate_held_out_set(
            training_vars=training_vars,
            schema_vars=schema_vars,
            output_path=self.output_file
        )
        
        training_set = set(held_out['training_variables'])
        held_out_set = set(held_out['held_out_variables'])
        
        # They should have no overlap
        self.assertEqual(len(training_set & held_out_set), 0)
        
        # Their union should equal schema variables
        self.assertEqual(training_set | held_out_set, schema_vars)

if __name__ == '__main__':
    import unittest
    unittest.main()
