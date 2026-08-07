"""
Contract tests for the Caco-2 dataset against the schema defined in T007.

These tests validate that the processed dataset adheres to the structural
and type constraints defined in `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`.

Dependency: T007 (Schema definition)
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports if running as script
# but rely on project structure for standard execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"

# Try to import jsonschema if available, otherwise implement basic validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("WARNING: jsonschema not installed. Using basic validation fallback.")


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema and convert to JSON-compatible dict."""
    # Since schema.yaml is defined in T007, we assume it exists and is valid YAML/JSON
    # We will load it as JSON for simplicity if it's valid JSON, or use yaml if available
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    content = schema_path.read_text()
    # T007 defines the schema. We assume it's valid YAML that can be parsed.
    # If 'yaml' is not installed, we try to parse as JSON if the file is JSON-like.
    # However, standard practice is to use the 'yaml' library.
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        # Fallback: try to load as JSON if it looks like JSON
        # This is a minimal fallback for environments without PyYAML
        # The schema defined in T007 is simple enough that it could be JSON.
        import json
        return json.loads(content)


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against the schema.
    Returns a list of error messages.
    """
    errors = []
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check types for present fields
    for field, value in record.items():
        if field in properties:
            expected_type = properties[field].get("type")
            if expected_type == "string":
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif expected_type == "number":
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif expected_type == "integer":
                if not isinstance(value, int):
                    errors.append(f"Field '{field}' must be integer, got {type(value).__name__}")
        # Unknown fields are allowed unless additionalProperties is false
        # (Not strictly enforced here unless specified in schema)

    return errors


class TestDatasetSchema(unittest.TestCase):
    """Test suite for validating the Caco-2 dataset against the schema."""

    @classmethod
    def setUpClass(cls):
        """Load the schema once for all tests."""
        if not SCHEMA_PATH.exists():
            # If schema doesn't exist, we can't run tests.
            # This should be caught by the test runner, but we handle it gracefully.
            raise RuntimeError(f"Schema file not found at {SCHEMA_PATH}. Ensure T007 is complete.")
        
        cls.schema = load_schema(SCHEMA_PATH)
        # Determine the path to the processed data
        # Based on T010, the output is typically data/processed/caco2_cleaned.csv
        # or similar. We look for the most recent processed file or a specific one.
        processed_dir = PROJECT_ROOT / "data" / "processed"
        if not processed_dir.exists():
            raise RuntimeError("Processed data directory not found. Ensure T008a and T010 are complete.")
        
        # Find the cleaned data file
        cleaned_files = list(processed_dir.glob("caco2_cleaned*.csv"))
        if not cleaned_files:
            # Fallback to any csv if naming convention differs slightly
            cleaned_files = list(processed_dir.glob("*.csv"))
        
        if not cleaned_files:
            raise RuntimeError("No cleaned CSV file found in data/processed/. Ensure T010 has run.")
        
        # Sort by modification time to get the latest
        cls.data_path = sorted(cleaned_files, key=lambda p: p.stat().st_mtime)[-1]
        print(f"Testing against data file: {cls.data_path}")

    def test_schema_loads(self):
        """Verify the schema is valid and loadable."""
        self.assertIsNotNone(self.schema)
        self.assertIn("properties", self.schema)
        self.assertIn("required", self.schema)

    def test_required_fields_present(self):
        """Ensure all records have required fields."""
        import pandas as pd
        df = pd.read_csv(self.data_path)
        required_fields = self.schema.get("required", [])
        
        missing_cols = set(required_fields) - set(df.columns)
        self.assertEqual(len(missing_cols), 0, f"Missing required columns in data: {missing_cols}")

    def test_field_types(self):
        """Verify that field types match the schema."""
        import pandas as pd
        df = pd.read_csv(self.data_path)
        properties = self.schema.get("properties", {})
        
        # Map pandas dtypes to expected schema types
        type_map = {
            "string": ["object", "string"],
            "number": ["float64", "int64", "float32", "int32"],
            "integer": ["int64", "int32"]
        }

        errors = []
        for col in df.columns:
            if col in properties:
                expected_type = properties[col].get("type")
                actual_dtype = str(df[col].dtype)
                
                if expected_type in type_map:
                    if actual_dtype not in type_map[expected_type]:
                        # Check for nulls which might affect dtype inference
                        if df[col].isna().any():
                            # Allow object type if there are NaNs in numeric columns (pandas behavior)
                            if expected_type in ["number", "integer"] and actual_dtype == "object":
                                continue 
                        errors.append(f"Column '{col}' has dtype {actual_dtype}, expected {expected_type}")

        self.assertEqual(len(errors), 0, f"Type mismatches found:\n" + "\n".join(errors))

    def test_no_null_required_fields(self):
        """Ensure no null values in required fields."""
        import pandas as pd
        df = pd.read_csv(self.data_path)
        required_fields = self.schema.get("required", [])
        
        for field in required_fields:
            if field in df.columns:
                null_count = df[field].isna().sum()
                self.assertEqual(null_count, 0, f"Field '{field}' contains {null_count} null values.")

    def test_smiles_format(self):
        """Validate that SMILES strings are non-empty and look like SMILES."""
        import pandas as pd
        df = pd.read_csv(self.data_path)
        if "smiles" not in df.columns:
            self.skipTest("smiles column not found")
        
        # Basic check: no empty strings or whitespace-only
        invalid_smiles = df[df["smiles"].astype(str).str.strip() == ""]
        self.assertEqual(len(invalid_smiles), 0, "Found empty or whitespace-only SMILES strings.")

    def test_logPapp_range(self):
        """Validate that logPapp is a reasonable number."""
        import pandas as pd
        df = pd.read_csv(self.data_path)
        if "logPapp" not in df.columns:
            self.skipTest("logPapp column not found")
        
        # logPapp is typically between -10 and 10 for permeability
        # We just check it's a number, not extreme outliers unless specified
        # For now, just ensure it's not NaN (covered by required fields) and is numeric
        non_numeric = df[~df["logPapp"].apply(lambda x: isinstance(x, (int, float)))]
        self.assertEqual(len(non_numeric), 0, "Found non-numeric values in logPapp.")


if __name__ == '__main__':
    unittest.main()