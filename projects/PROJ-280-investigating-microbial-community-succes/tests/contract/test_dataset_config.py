"""
Contract test for dataset schema validation (T009).
Validates that data/config/dataset_ids.json conforms to contracts/dataset-config.schema.yaml.
"""
import json
import os
import sys
import unittest
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError, SchemaError

# Project root relative to this test
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data" / "config" / "dataset_ids.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset-config.schema.yaml"

class TestDatasetConfigSchema(unittest.TestCase):
    """Contract tests for the dataset configuration JSON schema."""

    def setUp(self):
        """Load schema and config before each test."""
        if not SCHEMA_PATH.exists():
            self.fail(f"Schema file not found: {SCHEMA_PATH}")
        if not CONFIG_PATH.exists():
            self.fail(f"Config file not found: {CONFIG_PATH}")

        with open(SCHEMA_PATH, 'r') as f:
            self.schema = yaml.safe_load(f)

        with open(CONFIG_PATH, 'r') as f:
            self.config = json.load(f)

    def test_schema_is_valid_yaml(self):
        """Ensure the schema file itself is valid YAML."""
        self.assertIsInstance(self.schema, dict)
        self.assertIn('type', self.schema)
        self.assertEqual(self.schema['type'], 'object')

    def test_config_has_required_datasets_key(self):
        """Config must have a 'datasets' key."""
        self.assertIn('datasets', self.config)
        self.assertIsInstance(self.config['datasets'], list)

    def test_config_conforms_to_schema(self):
        """The config JSON must validate against the schema."""
        try:
            validate(instance=self.config, schema=self.schema)
        except ValidationError as e:
            self.fail(f"Config validation failed: {e.message}")
        except SchemaError as e:
            self.fail(f"Schema error: {e.message}")

    def test_dataset_entries_have_required_fields(self):
        """Each dataset entry must have id, source, and url."""
        required_fields = {'id', 'source', 'url'}
        for idx, ds in enumerate(self.config['datasets']):
            missing = required_fields - set(ds.keys())
            self.assertFalse(
                missing,
                f"Dataset at index {idx} is missing fields: {missing}"
            )

    def test_source_enum_values(self):
        """Source must be either 'NCBI_SRA' or 'Zenodo'."""
        valid_sources = {"NCBI_SRA", "Zenodo"}
        for idx, ds in enumerate(self.config['datasets']):
            self.assertIn(
                ds['source'],
                valid_sources,
                f"Dataset {idx} has invalid source: {ds['source']}"
            )

    def test_sra_id_format(self):
        """If source is NCBI_SRA, id must match SRR/ERR pattern."""
        import re
        sra_pattern = re.compile(r'^(SRR|ERR)[0-9]+$')
        for idx, ds in enumerate(self.config['datasets']):
            if ds['source'] == 'NCBI_SRA':
                self.assertTrue(
                    sra_pattern.match(ds['id']),
                    f"Dataset {idx} has invalid SRA ID format: {ds['id']}"
                )

    def test_zenodo_url_format(self):
        """If source is Zenodo, url must match Zenodo DOI pattern."""
        import re
        zenodo_pattern = re.compile(r'^10\.5281/zenodo\.[0-9]+$')
        for idx, ds in enumerate(self.config['datasets']):
            if ds['source'] == 'Zenodo':
                # The schema expects 'url' to be the DOI string for Zenodo
                # based on the provided schema snippet: url: string
                # and the regex VALID_ZENDO = r'^10\.5281/zenodo\.[0-9]+$'
                # The validator in validators.py checks 'url' against this.
                # We check the actual field 'url' here.
                self.assertTrue(
                    zenodo_pattern.match(ds['url']),
                    f"Dataset {idx} has invalid Zenodo URL format: {ds['url']}"
                )

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
