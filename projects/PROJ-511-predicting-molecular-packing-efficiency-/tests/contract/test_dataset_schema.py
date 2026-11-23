"""
Contract test for dataset schema validation (T010).

This test validates that the generated dataset (data/dataset.csv) strictly
adheres to the schema defined in contracts/dataset.schema.yaml (created in T004).

Dependencies:
- T004: contracts/dataset.schema.yaml must exist.
- T018: data/dataset.csv must exist and be generated.

This test ensures data integrity and prevents schema drift before the dataset
is used for model training (US2).
"""
import os
import sys
import json
import yaml
import unittest
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("WARNING: jsonschema not installed. Install with: pip install jsonschema")

# Constants
SCHEMA_PATH = project_root / "contracts" / "dataset.schema.yaml"
DATASET_PATH = project_root / "data" / "dataset.csv"

class TestDatasetSchema(unittest.TestCase):
    """Test suite for validating dataset schema compliance."""

    @classmethod
    def setUpClass(cls):
        """Load schema and dataset before running tests."""
        if not HAS_JSONSCHEMA:
            raise RuntimeError("jsonschema is required for contract tests.")

        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(
                f"Schema file not found: {SCHEMA_PATH}. "
                "Ensure T004 (contracts/dataset.schema.yaml) is completed."
            )

        if not DATASET_PATH.exists():
            raise FileNotFoundError(
                f"Dataset file not found: {DATASET_PATH}. "
                "Ensure T018 (data/dataset.csv) is completed before running this test."
            )

        # Load schema
        with open(SCHEMA_PATH, 'r') as f:
            cls.schema = yaml.safe_load(f)

        # Load dataset
        import pandas as pd
        cls.df = pd.read_csv(DATASET_PATH)
        cls.records = cls.df.to_dict(orient='records')

    def test_schema_exists(self):
        """Verify the schema file is valid YAML and has required structure."""
        self.assertIsInstance(self.schema, dict)
        self.assertIn("type", self.schema)
        self.assertEqual(self.schema["type"], "object")
        self.assertIn("properties", self.schema)

    def test_required_fields_present(self):
        """Verify all required fields defined in schema are present in dataset."""
        required_fields = self.schema.get("required", [])
        dataset_columns = set(self.df.columns)
        
        missing_fields = [field for field in required_fields if field not in dataset_columns]
        self.assertEqual(
            len(missing_fields), 0,
            f"Dataset missing required fields: {missing_fields}"
        )

    def test_row_count_minimum(self):
        """Verify dataset has sufficient rows (>= 500 as per US1 goal)."""
        self.assertGreaterEqual(
            len(self.df), 500,
            f"Dataset has only {len(self.df)} rows. Minimum required is 500."
        )

    def test_validate_each_record(self):
        """Validate every row in the dataset against the JSON schema."""
        errors = []
        
        for idx, record in enumerate(self.records):
            try:
                jsonschema.validate(instance=record, schema=self.schema)
            except jsonschema.ValidationError as e:
                errors.append({
                    "row_index": idx,
                    "cod_id": record.get("cod_id", "UNKNOWN"),
                    "message": e.message,
                    "path": list(e.path)
                })
                # Limit error collection to avoid huge test output
                if len(errors) >= 10:
                    break

        if errors:
            error_details = "\n".join([
                f"Row {e['row_index']} (COD: {e['cod_id']}): {e['message']}"
                for e in errors
            ])
            self.fail(f"Schema validation failed for {len(errors)} records:\n{error_details}")

    def test_cod_id_pattern(self):
        """Verify cod_id matches the pattern ^COD-\\d+$."""
        import re
        pattern = re.compile(r"^COD-\d+$")
        invalid_ids = [
            row["cod_id"] for row in self.records 
            if not pattern.match(str(row["cod_id"]))
        ]
        
        self.assertEqual(
            len(invalid_ids), 0,
            f"Found {len(invalid_ids)} invalid COD IDs: {invalid_ids[:5]}..."
        )

    def test_numeric_constraints(self):
        """Verify numeric fields respect min/max constraints."""
        invalid_records = []
        
        for idx, row in self.records:
            issues = []
            
            # unit_cell_volume > 0
            if row.get("unit_cell_volume", 0) <= 0:
                issues.append("unit_cell_volume <= 0")
            
            # n_atoms >= 1
            if row.get("n_atoms", 0) < 1:
                issues.append("n_atoms < 1")
            
            # raw_pc [0, 1]
            pc = row.get("raw_pc")
            if pc is not None and (pc < 0 or pc > 1):
                issues.append(f"raw_pc {pc} not in [0, 1]")
            
            # cape >= 0
            cape = row.get("cape")
            if cape is not None and cape < 0:
                issues.append(f"cape {cape} < 0")
            
            if issues:
                invalid_records.append({
                    "cod_id": row.get("cod_id"),
                    "issues": issues
                })

        self.assertEqual(
            len(invalid_records), 0,
            f"Numeric constraints violated in {len(invalid_records)} records: {invalid_records[:3]}"
        )

    def test_lattice_system_enum(self):
        """Verify lattice_system is a non-empty string (schema allows any string, but logically must be valid)."""
        # While schema just says string, we can check for empty strings which are likely errors
        empty_lattices = [
            row.get("cod_id") for row in self.records
            if not row.get("lattice_system") or not isinstance(row.get("lattice_system"), str)
        ]
        
        self.assertEqual(
            len(empty_lattices), 0,
            f"Found {len(empty_lattices)} records with missing or invalid lattice_system."
        )

    def test_smiles_source_enum(self):
        """Verify smiles_source is either 'extracted' or 'generated'."""
        valid_sources = {"extracted", "generated"}
        invalid_sources = [
            row.get("cod_id") for row in self.records
            if row.get("smiles_source") not in valid_sources
        ]
        
        self.assertEqual(
            len(invalid_sources), 0,
            f"Found {len(invalid_sources)} records with invalid smiles_source: {invalid_sources[:5]}"
        )

    def test_principal_moments_array(self):
        """Verify principal_moments is an array of 3 numbers."""
        invalid_moments = []
        for row in self.records:
            pm = row.get("principal_moments")
            if not isinstance(pm, list) or len(pm) != 3:
                invalid_moments.append(row.get("cod_id"))
            else:
                try:
                    # Ensure they are numbers
                    [float(x) for x in pm]
                except (TypeError, ValueError):
                    invalid_moments.append(row.get("cod_id"))
        
        self.assertEqual(
            len(invalid_moments), 0,
            f"Found {len(invalid_moments)} records with invalid principal_moments."
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
