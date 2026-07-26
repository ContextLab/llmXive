"""
Contract tests for the synthetic image schema.

This module validates that generated synthetic images and their annotations
strictly adhere to the schema defined in contracts/synthetic_image.schema.yaml.

It verifies:
1. Schema file existence and validity.
2. Validation of correct JSON structures against the schema.
3. Detection of invalid structures (missing fields, wrong types).
"""
import json
import os
import unittest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Import the validator utility from the project's contracts module
# This ensures we are testing the actual validation logic used in the pipeline
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.validator import validate_synthetic_image, validate_file


class TestSyntheticImageSchema(unittest.TestCase):
    """Contract tests for the synthetic image JSON schema."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.schema_path = self.project_root / "contracts" / "synthetic_image.schema.yaml"
        
        # Ensure schema file exists
        self.assertTrue(
            self.schema_path.exists(),
            f"Schema file not found at {self.schema_path}. "
            "Ensure T042 (schema definition) is completed."
        )

    def test_schema_file_is_valid_yaml(self):
        """Verify the schema file is a valid YAML document."""
        # The validator utility loads this internally, but we explicitly check here
        # to ensure the file is not corrupted.
        try:
            with open(self.schema_path, 'r') as f:
                import yaml
                schema = yaml.safe_load(f)
            self.assertIsInstance(schema, dict)
            self.assertIn('type', schema)
        except Exception as e:
            self.fail(f"Schema file is not valid YAML: {e}")

    def test_valid_sample_passes_validation(self):
        """Test that a correctly formatted synthetic image JSON passes validation."""
        # Construct a valid sample based on the schema requirements
        valid_sample = {
            "image_id": "sample_001",
            "source_image": "coco_stuff_12345.jpg",
            "region_count": 25,
            "regions": [
                {
                    "id": "region_1",
                    "bbox": [10.0, 20.0, 100.0, 100.0],
                    "label": "cat",
                    "spatial_relation": "left of"
                },
                {
                    "id": "region_2",
                    "bbox": [120.0, 20.0, 100.0, 100.0],
                    "label": "dog",
                    "spatial_relation": "right of"
                }
            ],
            "metadata": {
                "generator_version": "1.0.0",
                "seed": 42
            }
        }

        # This should not raise an exception
        try:
            validate_synthetic_image(valid_sample, self.schema_path)
        except ValidationError as e:
            self.fail(f"Valid sample failed schema validation: {e.message}")

    def test_missing_required_field_fails(self):
        """Test that a JSON missing a required field fails validation."""
        invalid_sample = {
            "image_id": "sample_002",
            # Missing 'region_count' which is required
            "regions": [],
            "metadata": {}
        }

        with self.assertRaises(ValidationError):
            validate_synthetic_image(invalid_sample, self.schema_path)

    def test_wrong_type_fails(self):
        """Test that a JSON with wrong data types fails validation."""
        invalid_sample = {
            "image_id": "sample_003",
            "region_count": "twenty-five",  # Should be integer
            "regions": [],
            "metadata": {}
        }

        with self.assertRaises(ValidationError):
            validate_synthetic_image(invalid_sample, self.schema_path)

    def test_file_validation_function_works(self):
        """Test the validate_file helper function with a temporary file."""
        valid_sample = {
            "image_id": "file_test_001",
            "region_count": 30,
            "regions": [],
            "metadata": {}
        }
        
        temp_file = self.project_root / "data" / "synthetic" / "temp_test.json"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write valid JSON
            with open(temp_file, 'w') as f:
                json.dump(valid_sample, f)
            
            # Should return True
            result = validate_file(str(temp_file), self.schema_path)
            self.assertTrue(result)

            # Write invalid JSON
            invalid_data = {"image_id": "bad"} # Missing required fields
            with open(temp_file, 'w') as f:
                json.dump(invalid_data, f)
            
            # Should return False (not raise, based on typical helper behavior)
            result = validate_file(str(temp_file), self.schema_path)
            self.assertFalse(result)
            
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_regions_structure_validation(self):
        """Test that regions list with invalid item structure fails."""
        invalid_sample = {
            "image_id": "sample_004",
            "region_count": 10,
            "regions": [
                {
                    "id": "region_1",
                    # Missing 'bbox', 'label', 'spatial_relation'
                }
            ],
            "metadata": {}
        }

        with self.assertRaises(ValidationError):
            validate_synthetic_image(invalid_sample, self.schema_path)


if __name__ == '__main__':
    unittest.main()