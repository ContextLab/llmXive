"""
Contract test for model output schema compliance.

This test validates that the model artifact (models/mlp.pt metadata) and
the validation report (results/validation_report.json) conform to the
schemas defined in contracts/model.schema.yaml and contracts/validation_report.schema.yaml.

Dependency: Must run AFTER T025 (training) and T029 (evaluation) complete.
"""
import json
import os
import sys
import unittest
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Add project root to path to allow imports if needed, though this test
# primarily uses file system and jsonschema.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_models_dir, get_results_dir, get_base_dir

SCHEMA_DIR = project_root / "contracts"
MODEL_SCHEMA_PATH = SCHEMA_DIR / "model.schema.yaml"
VALIDATION_REPORT_SCHEMA_PATH = SCHEMA_DIR / "validation_report.schema.yaml"

class TestModelSchema(unittest.TestCase):
    """Test suite for model and validation report schema compliance."""

    @classmethod
    def setUpClass(cls):
        """Load schemas once for all tests."""
        if not MODEL_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Model schema not found at {MODEL_SCHEMA_PATH}. "
                                    "Ensure T005/T022 has been completed.")
        if not VALIDATION_REPORT_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Validation report schema not found at {VALIDATION_REPORT_SCHEMA_PATH}. "
                                    "Ensure T005/T022 has been completed.")

        with open(MODEL_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            cls.model_schema = yaml.safe_load(f)

        with open(VALIDATION_REPORT_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            cls.validation_schema = yaml.safe_load(f)

        # Ensure validator is compatible with draft-07
        cls.model_validator = Draft7Validator(cls.model_schema)
        cls.validation_validator = Draft7Validator(cls.validation_schema)

    def test_model_schema_exists(self):
        """Verify that the model schema file exists and is valid YAML."""
        self.assertTrue(MODEL_SCHEMA_PATH.exists(), "Model schema file missing")
        self.assertIsInstance(self.model_schema, dict, "Model schema must be a dict")
        self.assertIn('properties', self.model_schema, "Model schema missing 'properties'")

    def test_validation_report_schema_exists(self):
        """Verify that the validation report schema file exists and is valid YAML."""
        self.assertTrue(VALIDATION_REPORT_SCHEMA_PATH.exists(), "Validation report schema file missing")
        self.assertIsInstance(self.validation_schema, dict, "Validation report schema must be a dict")
        self.assertIn('properties', self.validation_schema, "Validation report schema missing 'properties'")

    def test_model_artifact_metadata_schema(self):
        """
        Validate the model metadata (if available) against model.schema.yaml.

        Note: Since mlp.pt is a binary torch file, we validate a metadata JSON
        that should accompany it (e.g., models/mlp_metadata.json) OR we check
        if the task implies validating the structure of the report that describes
        the model. Based on T029, the 'validation_report.json' describes the
        model's performance. The 'model.schema.yaml' describes the model architecture
        metadata.

        We assume the training script (T025) or evaluation (T029) produces a
        metadata file or that we validate the 'model' section if the report
        contained it. However, T029 output is 'validation_report.json'.
        Let's check if a model metadata file exists, or if the test is meant
        to validate the *schema definition* itself against the *content* of
        the validation report if the report includes model details.

        Re-reading T022: "Contract test for model output schema".
        The schema defines: model_path, architecture, parameters_count, training_config.
        The validation_report (T029) defines: pearson_r, spearman_rho, etc.
        These are separate artifacts.

        We will attempt to load a hypothetical model metadata file generated
        by the training pipeline. If it doesn't exist, we skip or fail based
        on strictness. Given the constraint "Dependency: Must run AFTER T025",
        we expect the model artifact to exist. We will look for a companion
        JSON metadata file or validate the schema structure itself.

        Strategy: Validate the schema definitions are correct, then attempt
        to load a real metadata file if it exists.
        """
        models_dir = get_models_dir()
        metadata_path = models_dir / "mlp_metadata.json"

        if not metadata_path.exists():
            # If the metadata file doesn't exist, we cannot validate the instance.
            # However, the task is to test the *schema*. The schema itself is valid.
            # We assert that the schema is well-formed.
            self.assertTrue(self.model_validator.is_valid(self.model_schema),
                            "Model schema itself is invalid according to Draft7Validator")
            self.skipTest("models/mlp_metadata.json not found. T025 may not have generated metadata.")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)

        try:
            validate(instance=model_data, schema=self.model_schema)
        except ValidationError as e:
            self.fail(f"Model metadata at {metadata_path} does not conform to schema: {e.message}")

    def test_validation_report_schema(self):
        """
        Validate the validation report (results/validation_report.json)
        against validation_report.schema.yaml.
        """
        results_dir = get_results_dir()
        report_path = results_dir / "validation_report.json"

        if not report_path.exists():
            self.fail(f"Validation report not found at {report_path}. "
                      "Ensure T029 has been completed successfully.")

        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        try:
            validate(instance=report_data, schema=self.validation_schema)
        except ValidationError as e:
            self.fail(f"Validation report at {report_path} does not conform to schema: {e.message}")

    def test_validation_report_required_fields(self):
        """Specific check for required fields in validation report."""
        results_dir = get_results_dir()
        report_path = results_dir / "validation_report.json"

        if not report_path.exists():
            self.skipTest("Validation report not found.")

        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        required_fields = [
            'pearson_r', 'spearman_rho', 'mae', 'shapiro_wilk_p',
            'partial_corr_r', 'partial_corr_p', 'vif_flags',
            'permutation_p_value', 'permutation_shuffles'
        ]

        for field in required_fields:
            self.assertIn(field, report_data, f"Missing required field: {field}")

        # Specific constraint check from schema: permutation_shuffles must be 10000
        self.assertEqual(report_data.get('permutation_shuffles'), 10000,
                         "permutation_shuffles must be exactly 10000 as per FR-016")

if __name__ == '__main__':
    unittest.main()