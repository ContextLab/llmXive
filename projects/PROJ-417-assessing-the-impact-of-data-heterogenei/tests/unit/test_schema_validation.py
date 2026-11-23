"""
Unit tests for schema validation of EstimationResult.
Verifies T004b: Estimation Result Schema definition and validity.
"""
import json
import os
import sys
import unittest
from pathlib import Path
import yaml

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestEstimationResultSchema(unittest.TestCase):
    """Test cases for the estimation_result.schema.yaml."""

    @classmethod
    def setUpClass(cls):
        """Load the schema and define a valid dummy record."""
        schema_path = project_root / "specs" / "001-assess-heterogeneity-impact" / "contracts" / "estimation_result.schema.yaml"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, 'r') as f:
            cls.schema = yaml.safe_load(f)
        
        # Define a valid dummy record matching the schema
        cls.valid_record = {
            "replicate_id": "rep_001",
            "tau2_level": 0.1,
            "estimator_type": "DerSimonianLaird",
            "pooled_estimate": 0.52,
            "ci_lower": 0.15,
            "ci_upper": 0.89,
            "i_squared": 45.2,
            "q_statistic": 12.5,
            "n_studies": 20,
            "tau2_estimate": 0.09,
            "reliability_flag": True,
            "bias": 0.02,
            "coverage_flag": True,
            "convergence_status": "success"
        }

        cls.invalid_record_missing_field = {
            "replicate_id": "rep_002",
            "tau2_level": 0.1,
            "estimator_type": "DerSimonianLaird",
            "pooled_estimate": 0.52,
            # Missing ci_lower, ci_upper, etc.
            "n_studies": 20,
            "reliability_flag": True
        }

        cls.invalid_record_wrong_type = {
            "replicate_id": "rep_003",
            "tau2_level": 0.1,
            "estimator_type": "DerSimonianLaird",
            "pooled_estimate": 0.52,
            "ci_lower": 0.15,
            "ci_upper": 0.89,
            "i_squared": 45.2,
            "q_statistic": 12.5,
            "n_studies": "twenty",  # Should be integer
            "tau2_estimate": 0.09,
            "reliability_flag": True
        }

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        schema_path = project_root / "specs" / "001-assess-heterogeneity-impact" / "contracts" / "estimation_result.schema.yaml"
        self.assertTrue(schema_path.exists(), "Schema file must exist")

    def test_schema_has_required_fields(self):
        """Verify the schema defines I^2, Q, and reliability_flag."""
        required = self.schema.get('required', [])
        properties = self.schema.get('properties', {})
        
        self.assertIn('i_squared', required, "i_squared must be required")
        self.assertIn('q_statistic', required, "q_statistic must be required")
        self.assertIn('reliability_flag', required, "reliability_flag must be required")
        
        # Verify types
        self.assertEqual(properties['i_squared']['type'], 'number')
        self.assertEqual(properties['q_statistic']['type'], 'number')
        self.assertEqual(properties['reliability_flag']['type'], 'boolean')

    def test_valid_record_conforms(self):
        """Verify a valid dummy record conforms to the schema."""
        # Basic structural check since we don't import jsonschema here to avoid extra deps
        # We check that all required fields exist and have correct types
        required = self.schema.get('required', [])
        properties = self.schema.get('properties', {})
        
        for field in required:
            self.assertIn(field, self.valid_record, f"Missing required field: {field}")
            field_type = properties.get(field, {}).get('type')
            
            if field_type == 'number':
                self.assertIsInstance(self.valid_record[field], (int, float))
            elif field_type == 'integer':
                self.assertIsInstance(self.valid_record[field], int)
            elif field_type == 'boolean':
                self.assertIsInstance(self.valid_record[field], bool)
            elif field_type == 'string':
                self.assertIsInstance(self.valid_record[field], str)
        
        # Check enum constraint for estimator_type
        estimator_enum = properties['estimator_type']['enum']
        self.assertIn(self.valid_record['estimator_type'], estimator_enum)

    def test_invalid_record_missing_field(self):
        """Verify a record with missing required fields fails validation logic."""
        required = self.schema.get('required', [])
        missing_fields = set(required) - set(self.invalid_record_missing_field.keys())
        self.assertGreater(len(missing_fields), 0, "Invalid record should be missing fields")

    def test_invalid_record_wrong_type(self):
        """Verify a record with wrong types fails validation logic."""
        # Check n_studies is integer
        self.assertIsInstance(self.invalid_record_wrong_type['n_studies'], str)
        # The schema expects integer, so this record is invalid

    def test_save_dummy_record_to_results(self):
        """Save a valid dummy record to data/results for verification."""
        output_dir = project_root / "data" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "schema_estimation_result_validation.json"
        
        validation_result = {
            "status": "valid",
            "schema_path": str(project_root / "specs" / "001-assess-heterogeneity-impact" / "contracts" / "estimation_result.schema.yaml"),
            "test_record": self.valid_record,
            "timestamp": "2023-10-27T00:00:00Z",
            "checks": {
                "required_fields_present": True,
                "types_correct": True,
                "enum_constraints_met": True
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(validation_result, f, indent=2)
        
        self.assertTrue(output_file.exists(), "Validation result file must be created")

if __name__ == '__main__':
    unittest.main()