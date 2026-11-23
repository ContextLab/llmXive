"""
Contract tests validating data artifacts against YAML schemas.
"""
import json
import os
import sys
import unittest
from pathlib import Path

import yaml
import jsonschema

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

SCHEMAS_DIR = project_root / "contracts"
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"

class TestDatasetMetadataSchema(unittest.TestCase):
    """Validates data/raw/openml_metadata_filtered.json against dataset_metadata.schema.yaml"""

    def test_dataset_metadata_schema(self):
        schema_path = SCHEMAS_DIR / "dataset_metadata.schema.yaml"
        data_path = DATA_RAW_DIR / "openml_metadata_filtered.json"

        self.assertTrue(schema_path.exists(), f"Schema file missing: {schema_path}")
        self.assertTrue(data_path.exists(), f"Data file missing: {data_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list, "Root element of data file must be a list")
        self.assertGreater(len(data), 0, "Data file must contain at least one entry")

        for idx, entry in enumerate(data):
            try:
                jsonschema.validate(instance=entry, schema=schema)
            except jsonschema.ValidationError as e:
                self.fail(f"Validation error at index {idx}: {e.message}")

class TestExtractedParamsSchema(unittest.TestCase):
    """Validates data/processed/extracted_params.json against extracted_params.schema.yaml"""

    def test_extracted_params_schema(self):
        schema_path = SCHEMAS_DIR / "extracted_params.schema.yaml"
        data_path = DATA_PROCESSED_DIR / "extracted_params.json"

        if not schema_path.exists():
            self.skipTest(f"Schema file missing: {schema_path}")
        
        if not data_path.exists():
            self.skipTest(f"Data file missing: {data_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list, "Root element of data file must be a list")
        
        for idx, entry in enumerate(data):
            try:
                jsonschema.validate(instance=entry, schema=schema)
            except jsonschema.ValidationError as e:
                self.fail(f"Validation error at index {idx}: {e.message}")

class TestFinalReportSchema(unittest.TestCase):
    """Validates data/processed/audit_report.json against report.schema.yaml"""

    def test_final_report_schema(self):
        schema_path = SCHEMAS_DIR / "report.schema.yaml"
        data_path = DATA_PROCESSED_DIR / "audit_report.json"

        if not schema_path.exists():
            self.skipTest(f"Schema file missing: {schema_path}")

        if not data_path.exists():
            self.skipTest(f"Data file missing: {data_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Validation error: {e.message}")

if __name__ == "__main__":
    unittest.main()