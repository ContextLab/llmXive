"""
Integration test for distribution fit validation.
Verifies that the validation script correctly identifies valid and invalid data.
"""
import csv
import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate_distribution_fits import validate_row, load_schema

class TestDistributionValidation(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.schema_path = os.path.join(self.temp_dir, "schema.yaml")
        self.csv_path = os.path.join(self.temp_dir, "data.csv")
        
        # Create a minimal valid schema for testing
        schema_content = """
        type: object
        required:
          - game_id
          - distribution_family
          - KS_D
          - KS_pvalue
          - AIC
        properties:
          game_id:
            type: string
          distribution_family:
            type: string
            enum:
              - lognormal
              - weibull
              - gamma
          KS_D:
            type: number
            minimum: 0
          KS_pvalue:
            type: number
            minimum: 0
            maximum: 1
          AIC:
            type: number
        additionalProperties: false
        """
        with open(self.schema_path, 'w') as f:
            f.write(schema_content)
        
        self.schema = load_schema(self.schema_path)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_valid_row(self):
        """Test that a valid row passes validation."""
        valid_row = {
            "game_id": "test-game",
            "distribution_family": "lognormal",
            "KS_D": "0.05",
            "KS_pvalue": "0.8",
            "AIC": "100.5"
        }
        is_valid, msg = validate_row(valid_row, self.schema)
        self.assertTrue(is_valid, f"Valid row failed: {msg}")

    def test_missing_required_field(self):
        """Test that a row missing a required field fails."""
        invalid_row = {
            "game_id": "test-game",
            # Missing distribution_family
            "KS_D": "0.05",
            "KS_pvalue": "0.8",
            "AIC": "100.5"
        }
        is_valid, msg = validate_row(invalid_row, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("Missing required field", msg)

    def test_invalid_enum_value(self):
        """Test that a row with an invalid enum value fails."""
        invalid_row = {
            "game_id": "test-game",
            "distribution_family": "invalid_dist",
            "KS_D": "0.05",
            "KS_pvalue": "0.8",
            "AIC": "100.5"
        }
        is_valid, msg = validate_row(invalid_row, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("not in allowed values", msg)

    def test_number_out_of_range(self):
        """Test that a number outside the allowed range fails."""
        invalid_row = {
            "game_id": "test-game",
            "distribution_family": "lognormal",
            "KS_D": "-0.5", # Negative D is invalid
            "KS_pvalue": "0.8",
            "AIC": "100.5"
        }
        is_valid, msg = validate_row(invalid_row, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("below minimum", msg)

    def test_unexpected_field(self):
        """Test that an unexpected field fails when additionalProperties is false."""
        invalid_row = {
            "game_id": "test-game",
            "distribution_family": "lognormal",
            "KS_D": "0.05",
            "KS_pvalue": "0.8",
            "AIC": "100.5",
            "unexpected_field": "value"
        }
        is_valid, msg = validate_row(invalid_row, self.schema)
        self.assertFalse(is_valid)
        self.assertIn("Unexpected field", msg)

if __name__ == "__main__":
    unittest.main()