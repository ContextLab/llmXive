"""
Tests for the distribution fit validation script (T023).

This module validates that the validation script correctly:
1. Accepts valid data conforming to the schema.
2. Rejects data with missing required fields.
3. Rejects data with invalid types (e.g., non-numeric AIC).
4. Handles missing files gracefully.
"""
import csv
import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming this test runs from the project root or is configured correctly
# We simulate the environment by creating temp files
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_distribution_fits import validate_distribution_fits, load_schema, validate_row

class TestDistributionValidation(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.schema_path = Path(self.temp_dir) / "test_schema.yaml"
        self.data_path = Path(self.temp_dir) / "test_data.csv"
        self.report_path = Path(self.temp_dir) / "test_report.json"
        
        # Create a mock schema
        self.schema_content = """
        type: object
        properties:
          game_id:
            type: string
          distribution_family:
            type: string
          parameters:
            type: object
          KS_D:
            type: number
          KS_pvalue:
            type: number
          AIC:
            type: number
        required:
          - game_id
          - distribution_family
          - parameters
          - KS_D
          - KS_pvalue
          - AIC
        """
        with open(self.schema_path, 'w') as f:
            f.write(self.schema_content)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_validate_row_valid(self):
        """Test validation of a valid row."""
        schema = load_schema(self.schema_path)
        valid_row = {
            "game_id": "super-mario-64",
            "distribution_family": "log-normal",
            "parameters": '{"mu": 1.2, "sigma": 0.5}',
            "KS_D": "0.05",
            "KS_pvalue": "0.85",
            "AIC": "120.5"
        }
        errors = validate_row(valid_row, schema)
        self.assertEqual(len(errors), 0)

    def test_validate_row_missing_field(self):
        """Test validation fails on missing required field."""
        schema = load_schema(self.schema_path)
        invalid_row = {
            "game_id": "zelda-oot",
            "distribution_family": "weibull",
            # Missing parameters, KS_D, etc.
            "parameters": '{"k": 1.5}',
            "KS_D": "0.04",
            "KS_pvalue": "0.90",
            "AIC": "115.0"
        }
        errors = validate_row(invalid_row, schema)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Missing required field" in e for e in errors))

    def test_validate_row_invalid_type(self):
        """Test validation fails on non-numeric values for numeric fields."""
        schema = load_schema(self.schema_path)
        invalid_row = {
            "game_id": "metroid",
            "distribution_family": "gamma",
            "parameters": '{"alpha": 2.0, "beta": 0.5}',
            "KS_D": "0.05",
            "KS_pvalue": "invalid_float",
            "AIC": "130.0"
        }
        errors = validate_row(invalid_row, schema)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("must be numeric" in e for e in errors))

    def test_integration_valid_data(self):
        """Integration test with a valid CSV file."""
        # Write valid CSV
        with open(self.data_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "game_id", "distribution_family", "parameters", "KS_D", "KS_pvalue", "AIC"
            ])
            writer.writeheader()
            writer.writerow({
                "game_id": "mario",
                "distribution_family": "log-normal",
                "parameters": '{"mu": 1.0}',
                "KS_D": "0.05",
                "KS_pvalue": "0.8",
                "AIC": "100.0"
            })

        # Mock the global paths in the script
        import scripts.validate_distribution_fits as v_module
        original_schema = v_module.SCHEMA_PATH
        original_data = v_module.DATA_PATH
        original_report = v_module.OUTPUT_REPORT_PATH

        v_module.SCHEMA_PATH = self.schema_path
        v_module.DATA_PATH = self.data_path
        v_module.OUTPUT_REPORT_PATH = self.report_path

        try:
            success = v_module.validate_distribution_fits()
            self.assertTrue(success)
            self.assertTrue(self.report_path.exists())
            
            with open(self.report_path, 'r') as f:
                report = json.load(f)
            self.assertEqual(report["error_count"], 0)
            self.assertEqual(report["valid_records"], 1)
        finally:
            v_module.SCHEMA_PATH = original_schema
            v_module.DATA_PATH = original_data
            v_module.OUTPUT_REPORT_PATH = original_report

    def test_integration_invalid_data(self):
        """Integration test with an invalid CSV file."""
        # Write invalid CSV (missing AIC)
        with open(self.data_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "game_id", "distribution_family", "parameters", "KS_D", "KS_pvalue", "AIC"
            ])
            writer.writeheader()
            writer.writerow({
                "game_id": "mario",
                "distribution_family": "log-normal",
                "parameters": '{"mu": 1.0}',
                "KS_D": "0.05",
                "KS_pvalue": "0.8",
                "AIC": "" # Invalid
            })

        import scripts.validate_distribution_fits as v_module
        original_schema = v_module.SCHEMA_PATH
        original_data = v_module.DATA_PATH
        original_report = v_module.OUTPUT_REPORT_PATH

        v_module.SCHEMA_PATH = self.schema_path
        v_module.DATA_PATH = self.data_path
        v_module.OUTPUT_REPORT_PATH = self.report_path

        try:
            success = v_module.validate_distribution_fits()
            self.assertFalse(success)
            self.assertTrue(self.report_path.exists())
            
            with open(self.report_path, 'r') as f:
                report = json.load(f)
            self.assertGreater(report["error_count"], 0)
            self.assertEqual(report["valid_records"], 0)
        finally:
            v_module.SCHEMA_PATH = original_schema
            v_module.DATA_PATH = original_data
            v_module.OUTPUT_REPORT_PATH = original_report

    def test_missing_data_file(self):
        """Test behavior when data file is missing."""
        import scripts.validate_distribution_fits as v_module
        original_schema = v_module.SCHEMA_PATH
        original_data = v_module.DATA_PATH
        original_report = v_module.OUTPUT_REPORT_PATH

        v_module.SCHEMA_PATH = self.schema_path
        v_module.DATA_PATH = Path("/nonexistent/file.csv")
        v_module.OUTPUT_REPORT_PATH = self.report_path

        try:
            success = v_module.validate_distribution_fits()
            self.assertFalse(success)
        finally:
            v_module.SCHEMA_PATH = original_schema
            v_module.DATA_PATH = original_data
            v_module.OUTPUT_REPORT_PATH = original_report

if __name__ == "__main__":
    unittest.main()