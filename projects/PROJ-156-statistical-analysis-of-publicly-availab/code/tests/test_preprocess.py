import json
import os
import sys
import csv
import tempfile
import shutil
import unittest
from pathlib import Path

# Add the code directory to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from scripts.preprocess import load_schema, validate_record

class TestPreprocess(unittest.TestCase):
    """
    Unit tests for preprocessing logic, specifically focusing on contract validation.
    """

    def setUp(self):
        """Set up temporary directories and load the real schema."""
        self.temp_dir = tempfile.mkdtemp()
        self.schema_path = project_root / "contracts" / "run_record.schema.yaml"
        
        if not self.schema_path.exists():
            self.skipTest(f"Schema file not found at {self.schema_path}")
        
        self.schema = load_schema(self.schema_path)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_schema_success(self):
        """Verify that the real schema loads correctly."""
        self.assertIsNotNone(self.schema)
        self.assertIn("properties", self.schema)
        self.assertIn("required", self.schema)

    def test_validate_record_valid(self):
        """Test validation of a record that conforms to the schema."""
        valid_record = {
            "run_time_seconds": 1234.5,
            "runner_id": "a" * 64,  # 64 hex chars for SHA-256
            "attempt_number": 1,
            "category": "any%",
            "submission_date": "2023-10-27T10:00:00Z",
            "game_id": "super-mario-64",
            "total_prior_runs": 0,
            "time_since_first_run_days": 0.0,
            "lagged_competitive_pressure": 5
        }
        
        is_valid, error_msg = validate_record(valid_record, self.schema)
        self.assertTrue(is_valid, f"Valid record failed validation: {error_msg}")

    def test_validate_record_missing_field(self):
        """Test validation of a record missing a required field."""
        invalid_record = {
            "run_time_seconds": 1234.5,
            "runner_id": "a" * 64,
            "attempt_number": 1,
            "category": "any%",
            "submission_date": "2023-10-27T10:00:00Z",
            # Missing game_id
        }
        
        is_valid, error_msg = validate_record(invalid_record, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("game_id", error_msg)

    def test_validate_record_invalid_type(self):
        """Test validation of a record with an incorrect type."""
        invalid_record = {
            "run_time_seconds": "not_a_number",  # Should be number
            "runner_id": "a" * 64,
            "attempt_number": 1,
            "category": "any%",
            "submission_date": "2023-10-27T10:00:00Z",
            "game_id": "super-mario-64"
        }
        
        is_valid, error_msg = validate_record(invalid_record, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("run_time_seconds", error_msg)

    def test_validate_record_invalid_runner_id_format(self):
        """Test validation of a runner_id that is not a valid SHA-256 hash."""
        invalid_record = {
            "run_time_seconds": 1234.5,
            "runner_id": "short_hash",  # Too short, not hex
            "attempt_number": 1,
            "category": "any%",
            "submission_date": "2023-10-27T10:00:00Z",
            "game_id": "super-mario-64"
        }
        
        is_valid, error_msg = validate_record(invalid_record, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("runner_id", error_msg)

    def test_contract_validation_integration(self):
        """
        Integration test: Ensure the schema file exists and can be used
        to validate a batch of records loaded from a CSV (simulating T013a output).
        """
        # Create a mock CSV file in the temp directory
        csv_path = os.path.join(self.temp_dir, "mock_records.csv")
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "run_time_seconds", "runner_id", "attempt_number", 
                "category", "submission_date", "game_id",
                "total_prior_runs", "time_since_first_run_days", "lagged_competitive_pressure"
            ])
            writer.writeheader()
            writer.writerow({
                "run_time_seconds": 500.0,
                "runner_id": "b" * 64,
                "attempt_number": 1,
                "category": "any%",
                "submission_date": "2023-01-01T00:00:00Z",
                "game_id": "zelda-oot",
                "total_prior_runs": 0,
                "time_since_first_run_days": 0.0,
                "lagged_competitive_pressure": 10
            })
            writer.writerow({
                "run_time_seconds": 600.0,
                "runner_id": "c" * 64,
                "attempt_number": 2,
                "category": "any%",
                "submission_date": "2023-01-02T00:00:00Z",
                "game_id": "zelda-oot",
                "total_prior_runs": 1,
                "time_since_first_run_days": 1.0,
                "lagged_competitive_pressure": 12
            })

        # Validate each row
        valid_count = 0
        invalid_count = 0
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to appropriate types for validation
                row["run_time_seconds"] = float(row["run_time_seconds"])
                row["attempt_number"] = int(row["attempt_number"])
                row["total_prior_runs"] = int(row["total_prior_runs"])
                row["time_since_first_run_days"] = float(row["time_since_first_run_days"])
                row["lagged_competitive_pressure"] = int(row["lagged_competitive_pressure"])
                
                is_valid, _ = validate_record(row, self.schema)
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

        # We expect all mock records to be valid
        self.assertEqual(invalid_count, 0)
        self.assertEqual(valid_count, 2)

    def test_run_record_schema_contract(self):
        """
        Contract test: Explicitly verify the schema contains all required fields
        defined in the task specification (T004).
        """
        required_fields = [
            "run_time_seconds", "runner_id", "attempt_number", 
            "category", "submission_date", "game_id"
        ]
        
        schema_required = self.schema.get("required", [])
        
        for field in required_fields:
            self.assertIn(field, schema_required, f"Required field '{field}' missing from schema")
        
        # Verify types
        props = self.schema.get("properties", {})
        self.assertEqual(props["run_time_seconds"]["type"], "number")
        self.assertEqual(props["runner_id"]["type"], "string")
        self.assertEqual(props["attempt_number"]["type"], "integer")

    def test_preprocessed_output_structure(self):
        """
        Test that the schema enforces the structure required for downstream tasks (T027).
        Specifically checks for the presence of 'lagged_competitive_pressure'.
        """
        self.assertIn("lagged_competitive_pressure", self.schema["properties"])
        self.assertEqual(self.schema["properties"]["lagged_competitive_pressure"]["type"], "integer")
        self.assertIn("lagged_competitive_pressure", self.schema["properties"]) # Redundant but explicit

if __name__ == "__main__":
    unittest.main()