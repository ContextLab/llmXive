"""
Contract tests for schema validation of cleaned studies and effect sizes.
Verifies that generated artifacts conform to contracts/cleaned_study.schema.yaml
and contracts/effect_size.schema.yaml.
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import yaml
from jsonschema import validate, ValidationError, SchemaError

class TestSchemaContracts(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Load schema definitions once."""
        contracts_dir = project_root / "contracts"
        cls.cleaned_study_schema_path = contracts_dir / "cleaned_study.schema.yaml"
        cls.effect_size_schema_path = contracts_dir / "effect_size.schema.yaml"
        
        if not cls.cleaned_study_schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {cls.cleaned_study_schema_path}")
        if not cls.effect_size_schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {cls.effect_size_schema_path}")

        with open(cls.cleaned_study_schema_path, "r") as f:
            cls.cleaned_study_schema = yaml.safe_load(f)
        
        with open(cls.effect_size_schema_path, "r") as f:
            cls.effect_size_schema = yaml.safe_load(f)

    def test_cleaned_study_schema_syntax(self):
        """Verify cleaned_study.schema.yaml is valid YAML and JSON Schema."""
        try:
            validate(instance={"id": "test"}, schema=self.cleaned_study_schema)
            # If it validates against itself (with dummy data), structure is sound
            # We just check it loads and has required keys
            self.assertIn("type", self.cleaned_study_schema)
            self.assertEqual(self.cleaned_study_schema["type"], "object")
            self.assertIn("properties", self.cleaned_study_schema)
            self.assertIn("delivery_format", self.cleaned_study_schema["properties"])
            self.assertIn("social_skill_domain", self.cleaned_study_schema["properties"])
        except SchemaError as e:
            self.fail(f"cleaned_study.schema.yaml is not a valid JSON Schema: {e}")

    def test_effect_size_schema_syntax(self):
        """Verify effect_size.schema.yaml is valid YAML and JSON Schema."""
        try:
            validate(instance={"study_id": "test"}, schema=self.effect_size_schema)
            self.assertIn("type", self.effect_size_schema)
            self.assertEqual(self.effect_size_schema["type"], "object")
            self.assertIn("properties", self.effect_size_schema)
            self.assertIn("hedges_g", self.effect_size_schema["properties"])
            self.assertIn("n_treatment", self.effect_size_schema["properties"])
        except SchemaError as e:
            self.fail(f"effect_size.schema.yaml is not a valid JSON Schema: {e}")

    def test_cleaned_study_enum_values(self):
        """Verify enum constraints in cleaned_study schema."""
        delivery_format_enum = self.cleaned_study_schema["properties"]["delivery_format"]["enum"]
        expected_formats = ["caregiver-mediated", "child-led", "mixed", "not-reported"]
        self.assertCountEqual(delivery_format_enum, expected_formats, 
                              "delivery_format enum must match Constitution Principle VII")

        domain_enum = self.cleaned_study_schema["properties"]["social_skill_domain"]["enum"]
        expected_domains = ["communication", "peer interaction", "emotional regulation", "mixed"]
        self.assertCountEqual(domain_enum, expected_domains,
                              "social_skill_domain enum must match FR-010")

    def test_effect_size_numeric_constraints(self):
        """Verify numeric constraints in effect_size schema."""
        se_props = self.effect_size_schema["properties"]["se"]
        self.assertIn("minimum", se_props)
        self.assertEqual(se_props["minimum"], 0, "SE must be non-negative")

        n_treatment_props = self.effect_size_schema["properties"]["n_treatment"]
        self.assertIn("minimum", n_treatment_props)
        self.assertEqual(n_treatment_props["minimum"], 1, "N must be at least 1")

    def test_instance_validation_cleaned_study(self):
        """Validate a realistic instance against the cleaned_study schema."""
        valid_instance = {
            "id": "NCT12345678",
            "title": "Mindfulness for ASD",
            "registry": "ClinicalTrials.gov",
            "age_range": "8-12",
            "diagnosis": "DSM-5",
            "outcomes": ["SRS-2", "ABC"],
            "intervention_components": ["breathing", "body scan"],
            "delivery_format": "caregiver-mediated",
            "follow_up": "3 months",
            "abstract_text": "This study investigates...",
            "social_skill_domain": "peer interaction"
        }
        try:
            validate(instance=valid_instance, schema=self.cleaned_study_schema)
        except ValidationError as e:
            self.fail(f"Valid instance failed schema validation: {e.message}")

    def test_instance_validation_effect_size(self):
        """Validate a realistic instance against the effect_size schema."""
        valid_instance = {
            "study_id": "NCT12345678",
            "hedges_g": 0.45,
            "se": 0.12,
            "ci_lower": 0.21,
            "ci_upper": 0.69,
            "n_treatment": 20,
            "n_control": 22
        }
        try:
            validate(instance=valid_instance, schema=self.effect_size_schema)
        except ValidationError as e:
            self.fail(f"Valid instance failed schema validation: {e.message}")

if __name__ == "__main__":
    unittest.main()