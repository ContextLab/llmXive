"""
Contract tests for JSON output schemas.

Validates that generated output files conform to their respective JSON Schema definitions.
"""
import json
import os
import unittest
from pathlib import Path
from typing import Dict, Any

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    # Fallback for environments where jsonschema might not be installed yet,
    # though requirements.txt should include it.
    jsonschema = None
    ValidationError = Exception

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "schemas"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class BaseSchemaTest(unittest.TestCase):
    """Base class for schema validation tests."""
    
    def load_schema(self, schema_filename: str) -> Dict[str, Any]:
        """Load a JSON schema from the specs directory."""
        schema_path = SCHEMAS_DIR / schema_filename
        self.assertTrue(schema_path.exists(), f"Schema file not found: {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_output(self, output_filename: str) -> Dict[str, Any]:
        """Load an output JSON file from the processed directory."""
        output_path = PROCESSED_DIR / output_filename
        # If file doesn't exist yet, this test might be skipped or failed depending on pipeline state
        if not output_path.exists():
            self.skipTest(f"Output file not found: {output_path}. Run the pipeline first.")
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any], schema_name: str):
        """Validate data against a schema using jsonschema."""
        if jsonschema is None:
            self.skipTest("jsonschema library not installed")
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            self.fail(f"Validation failed for {schema_name}: {e.message} at path {list(e.path)}")


class TestSimilarityReportSchema(BaseSchemaTest):
    """Contract test for similarity_report.schema.yaml (T009)."""

    def test_similarity_report_schema(self):
        schema = self.load_schema("similarity_report.schema.yaml")
        # Note: This test assumes the file exists. If T014 failed, this might be missing.
        # We check existence in load_schema.
        output_path = PROCESSED_DIR / "similarity_matrix.json"
        if not output_path.exists():
            self.skipTest("similarity_matrix.json not found. Run US1 pipeline.")
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.validate_against_schema(data, schema, "similarity_report")


class TestTokenAttributionSchema(BaseSchemaTest):
    """Contract test for token_attribution.schema.yaml (T016)."""

    def test_token_attribution_schema(self):
        schema = self.load_schema("token_attribution.schema.yaml")
        output_path = PROCESSED_DIR / "token_attribution_report.json"
        if not output_path.exists():
            self.skipTest("token_attribution_report.json not found. Run US2 pipeline.")

        with open(output_path, 'r') as f:
            data = json.load(f)

        self.validate_against_schema(data, schema, "token_attribution")


class TestPermutationResultSchema(BaseSchemaTest):
    """Contract test for permutation_result.schema.yaml (T024)."""

    def test_permutation_result_schema(self):
        """
        Validates that data/processed/permutation_result.json conforms to
        specs/schemas/permutation_result.schema.yaml.
        """
        schema = self.load_schema("permutation_result.schema.yaml")
        output_path = PROCESSED_DIR / "permutation_result.json"
        
        if not output_path.exists():
            self.skipTest("permutation_result.json not found. Run US3 statistical test pipeline.")

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.validate_against_schema(data, schema, "permutation_result")


class TestWalsValidationSchema(BaseSchemaTest):
    """Contract test for wals_validation.schema.yaml (T008)."""

    def test_wals_validation_schema(self):
        schema = self.load_schema("wals_validation.schema.yaml")
        output_path = PROCESSED_DIR / "wals_validation.json"
        
        if not output_path.exists():
            self.skipTest("wals_validation.json not found. Run US3 external validation pipeline.")

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.validate_against_schema(data, schema, "wals_validation")


if __name__ == "__main__":
    unittest.main()