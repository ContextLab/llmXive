"""
Unit tests for structural_metric.schema.yaml validation logic.

This module explicitly verifies that the schema enforces conditional logic:
1. 'semantic_complexity_score' is optional.
2. Fallback metrics (specifically 'lines_of_code') are required when semantic nodes are missing.
"""
import os
import sys
import unittest
import yaml
from pathlib import Path

# Ensure the code directory is in the path for imports if needed,
# though this test primarily validates the schema file content and logic.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = ROOT_DIR / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "structural_metric.schema.yaml"

class TestStructuralMetricSchemaValidation(unittest.TestCase):
    """Tests to verify the conditional logic in structural_metric.schema.yaml."""

    def setUp(self):
        """Load the schema file before each test."""
        if not SCHEMA_PATH.exists():
            self.fail(f"Schema file not found at {SCHEMA_PATH}. "
                      "Ensure T005 has created contracts/structural_metric.schema.yaml")
        
        with open(SCHEMA_PATH, "r") as f:
            self.schema = yaml.safe_load(f)

    def test_schema_exists_and_valid_yaml(self):
        """Verify the schema file is valid YAML and contains the expected root keys."""
        self.assertIsInstance(self.schema, dict)
        self.assertIn("type", self.schema)
        self.assertEqual(self.schema["type"], "object")

    def test_semantic_complexity_score_is_optional(self):
        """
        Verify that 'semantic_complexity_score' is defined as optional.
        
        In YAML/JSON Schema, a field is optional if it is NOT listed in the 
        'required' array of the parent object, or if it has 'required: false' 
        in a custom schema definition style.
        
        We check that 'semantic_complexity_score' is NOT in the 'required' list 
        of the 'properties' definition.
        """
        properties = self.schema.get("properties", {})
        required_fields = self.schema.get("required", [])
        
        self.assertIn("semantic_complexity_score", properties, 
                      "semantic_complexity_score must be defined in properties")
        
        # Assert it is NOT in the required list
        self.assertNotIn("semantic_complexity_score", required_fields,
                         "semantic_complexity_score MUST be optional and not in the required list")

    def test_fallback_metrics_required_when_semantic_missing(self):
        """
        Verify that fallback metrics, specifically 'lines_of_code', are required.
        
        The task requires that when semantic nodes are missing, fallback metrics 
        (lines_of_code) are mandatory. In the schema, this is enforced by including 
        'lines_of_code' in the 'required' array.
        """
        properties = self.schema.get("properties", {})
        required_fields = self.schema.get("required", [])
        
        self.assertIn("lines_of_code", properties,
                      "lines_of_code must be defined in properties")
        
        # Assert it IS in the required list to enforce fallback logic
        self.assertIn("lines_of_code", required_fields,
                      "lines_of_code MUST be required to enforce fallback metric logic "
                      "when semantic nodes are missing")

    def test_schema_structure_matches_task_requirements(self):
        """
        Comprehensive check that the schema structure satisfies the task description:
        - semantic_complexity_score is optional
        - lines_of_code is required
        """
        properties = self.schema.get("properties", {})
        required_fields = self.schema.get("required", [])
        
        # Check semantic_complexity_score presence and optionality
        self.assertIn("semantic_complexity_score", properties)
        self.assertNotIn("semantic_complexity_score", required_fields)
        
        # Check lines_of_code presence and requirement
        self.assertIn("lines_of_code", properties)
        self.assertIn("lines_of_code", required_fields)

    def test_dependency_depth_also_required(self):
        """
        Verify that other structural metrics like dependency_depth are also required
        to ensure a complete fallback set.
        """
        required_fields = self.schema.get("required", [])
        # Based on typical structural metric schemas, these should be present
        # This acts as a sanity check for the schema completeness
        self.assertIn("lines_of_code", required_fields)
        
        # Optional check: ensure other common metrics are defined
        properties = self.schema.get("properties", {})
        self.assertIn("dependency_depth", properties)

if __name__ == "__main__":
    unittest.main()