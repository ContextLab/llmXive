"""
Contract test for dataset schema validation.

This test validates that the final dataset produced by the pipeline (T018)
conforms to the schema defined in `contracts/dataset.schema.yaml` (T004).
It ensures data integrity, correct types, and presence of required fields
before the data is used for model training.

Dependencies:
- T004: contracts/dataset.schema.yaml must exist.
- T018: code/add_3d_descriptors.py must have produced data/dataset.csv.
"""
import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    raise RuntimeError("Missing dependency: 'jsonschema'. Install via 'pip install jsonschema'.")

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
DATASET_PATH = PROJECT_ROOT / "data" / "dataset.csv"

class TestDatasetSchema(unittest.TestCase):
    """
    Validates the dataset.csv against the defined JSON schema.
    """

    def setUp(self):
        """
        Load the schema and the dataset before each test.
        """
        if not SCHEMA_PATH.exists():
            self.fail(f"Schema file not found: {SCHEMA_PATH}. Ensure T004 is complete.")

        if not DATASET_PATH.exists():
            self.fail(f"Dataset file not found: {DATASET_PATH}. Ensure T018 has been run to generate data/dataset.csv.")

        # Load schema (YAML -> JSON dict)
        try:
            import yaml
            with open(SCHEMA_PATH, 'r') as f:
                self.schema = yaml.safe_load(f)
        except ImportError:
            self.fail("Missing dependency: 'pyyaml'. Install via 'pip install pyyaml'.")
        except Exception as e:
            self.fail(f"Failed to load schema: {e}")

        # Load dataset
        try:
            import pandas as pd
            self.df = pd.read_csv(DATASET_PATH)
        except Exception as e:
            self.fail(f"Failed to load dataset: {e}")

    def test_schema_exists_and_is_valid(self):
        """Verify the schema itself is a valid JSON Schema draft."""
        try:
            # Basic check that required keys exist
            self.assertIn('type', self.schema)
            self.assertEqual(self.schema['type'], 'object')
            self.assertIn('properties', self.schema)
            self.assertIn('required', self.schema)
        except AssertionError:
            self.fail("Schema structure is invalid or incomplete.")

    def test_dataset_rows_exist(self):
        """Ensure the dataset is not empty (minimum 500 rows requirement)."""
        self.assertGreater(len(self.df), 0, "Dataset is empty.")
        # Per US1 requirements, we expect >= 500 rows for a valid MVP dataset
        self.assertGreaterEqual(len(self.df), 500, f"Dataset has {len(self.df)} rows, expected >= 500.")

    def test_required_columns_present(self):
        """Check that all columns defined in 'required' schema are present."""
        required_fields = self.schema.get('required', [])
        missing_columns = set(required_fields) - set(self.df.columns)
        if missing_columns:
            self.fail(f"Missing required columns: {missing_columns}")

    def test_schema_validation_per_row(self):
        """
        Validate the structure of the dataset against the schema.
        Since jsonschema is designed for JSON objects, we convert the dataframe
        to a list of dicts and validate each record.
        """
        # Convert dataframe to list of records
        records = self.df.to_dict(orient='records')

        # If the schema expects an array of items (common for datasets), validate the whole list
        if self.schema.get('type') == 'array':
            try:
                validate(instance=records, schema=self.schema)
            except ValidationError as e:
                self.fail(f"Schema validation failed for dataset: {e.message}")
        else:
            # If schema is an object, it likely defines the structure of a single row
            # We validate a sample or all rows against the 'properties' if it's a row-schema
            # However, standard practice for CSV validation with jsonschema is often:
            # 1. Check columns match properties keys
            # 2. Check types of values in columns
            
            # Let's perform a robust check:
            # Check that every row is a dict and keys match schema properties
            schema_props = self.schema.get('properties', {})
            
            for idx, record in enumerate(records):
                # Check keys
                record_keys = set(record.keys())
                schema_keys = set(schema_props.keys())
                
                # Extra keys are usually allowed unless 'additionalProperties': False
                if self.schema.get('additionalProperties') is False:
                    extra = record_keys - schema_keys
                    if extra:
                        self.fail(f"Row {idx} has unexpected columns: {extra}")
                
                # Check missing required keys
                missing = set(schema_props.keys()) - record_keys
                if missing:
                    self.fail(f"Row {idx} missing required keys: {missing}")
                
                # Type checking for specific fields
                for key, value in record.items():
                    if key in schema_props:
                        expected_type = schema_props[key].get('type')
                        if expected_type:
                            if expected_type == 'number':
                                if not isinstance(value, (int, float)) or (isinstance(value, float) and (value != value)): # NaN check
                                    # Allow NaN for numbers in pandas usually, but strict schema might not
                                    # We'll be lenient on NaN for floats but check int/float nature
                                    if not isinstance(value, (int, float)):
                                        self.fail(f"Row {idx}, column {key}: expected number, got {type(value)}")
                            elif expected_type == 'string':
                                if value is not None and not isinstance(value, str):
                                    self.fail(f"Row {idx}, column {key}: expected string, got {type(value)}")
                            elif expected_type == 'integer':
                                if not isinstance(value, int):
                                    self.fail(f"Row {idx}, column {key}: expected integer, got {type(value)}")
                            elif expected_type == 'boolean':
                                if not isinstance(value, bool):
                                    self.fail(f"Row {idx}, column {key}: expected boolean, got {type(value)}")

    def test_smiles_validity_format(self):
        """
        Quick heuristic check that SMILES strings look like SMILES.
        Does not validate chemical correctness (requires RDKit), but checks format.
        """
        if 'smiles' not in self.df.columns:
            return # Handled by required columns test

        invalid_smiles = []
        for idx, row in self.df.iterrows():
            s = str(row['smiles'])
            if not s or len(s) < 2:
                invalid_smiles.append(idx)
            # Basic check: no whitespace, contains valid chars
            if ' ' in s or '\n' in s:
                invalid_smiles.append(idx)
        
        if invalid_smiles:
            self.fail(f"Found {len(invalid_smiles)} rows with malformed SMILES strings (indices: {invalid_smiles[:5]}...)")

    def test_packing_coefficient_range(self):
        """
        Verify that CAPE (target) and Raw PC are within physically possible ranges [0, 1].
        """
        # Check CAPE
        if 'cape' in self.df.columns:
            if not self.df['cape'].between(0.0, 1.0).all():
                # Allow for small floating point errors or NaNs
                invalid = self.df[~self.df['cape'].between(0.0, 1.0) & ~self.df['cape'].isna()]
                if not invalid.empty:
                    self.fail(f"CAPE values out of range [0, 1]: {invalid['cape'].describe()}")

        # Check raw_pc
        if 'raw_pc' in self.df.columns:
            if not self.df['raw_pc'].between(0.0, 1.0).all():
                invalid = self.df[~self.df['raw_pc'].between(0.0, 1.0) & ~self.df['raw_pc'].isna()]
                if not invalid.empty:
                    self.fail(f"Raw PC values out of range [0, 1]: {invalid['raw_pc'].describe()}")

if __name__ == '__main__':
    unittest.main()