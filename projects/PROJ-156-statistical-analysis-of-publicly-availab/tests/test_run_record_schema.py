"""
Unit test for the RunRecord JSON‑Schema contract.

The test loads the schema from ``contracts/run_record.schema.yaml`` and
validates a minimal but complete example record against it using
``jsonschema.validate``.
"""
import unittest
import pathlib
import yaml
import jsonschema

class TestRunRecordSchema(unittest.TestCase):
    """Validate that a sample RunRecord conforms to the JSON‑Schema."""

    def setUp(self):
        # Load the schema once for all tests.
        schema_path = pathlib.Path("contracts/run_record.schema.yaml")
        with schema_path.open("r", encoding="utf-8") as f:
            self.schema = yaml.safe_load(f)

        # Minimal valid record – matches the required fields in the schema.
        self.valid_record = {
            "run_time_seconds": 123.45,
            "runner_id": "a" * 64,                     # 64‑character hex string
            "attempt_number": 1,
            "category": "any%",
            "submission_date": "2023-01-01T12:00:00Z",
            "game_id": "test-game"
            # Optional fields are omitted intentionally.
        }

    def test_valid_record_passes(self):
        """A correctly‑formed record must validate without error."""
        try:
            jsonschema.validate(instance=self.valid_record, schema=self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Validation failed unexpectedly: {e}")

    def test_missing_required_field_fails(self):
        """Omitting a required field should raise a ValidationError."""
        incomplete = self.valid_record.copy()
        incomplete.pop("run_time_seconds")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=incomplete, schema=self.schema)

if __name__ == "__main__":
    unittest.main()