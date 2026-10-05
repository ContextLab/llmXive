import json
import os
import sys
import csv
import tempfile
import shutil
import unittest
from pathlib import Path
import jsonschema

# Ensure parent code directory is in path for imports if running standalone
# In CI/pytest context, this is usually handled by the runner or setup.cfg
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestPreprocess(unittest.TestCase):
    """
    Contract test for run_record.schema.yaml validation.
    Verifies that data/processed/run_records.csv conforms to the schema
    defined in contracts/run_record.schema.yaml.
    """

    def setUp(self):
        """
        Set up test fixtures.
        Locate the schema file and the expected processed data file.
        """
        self.project_root = Path(__file__).parent.parent
        self.schema_path = self.project_root / "contracts" / "run_record.schema.yaml"
        self.data_path = self.project_root / "data" / "processed" / "run_records.csv"
        
        # Ensure directories exist for test context if running in isolation
        # (Though in a real run, these should be created by T013a)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.schema_path.parent.mkdir(parents=True, exist_ok=True)

    def test_schema_file_exists(self):
        """Assert that the contract schema file exists."""
        self.assertTrue(
            self.schema_path.exists(),
            f"Schema file not found at {self.schema_path}. "
            "Ensure T004 has been completed and the file exists."
        )

    def test_data_file_exists(self):
        """Assert that the processed data file exists."""
        self.assertTrue(
            self.data_path.exists(),
            f"Processed data file not found at {self.data_path}. "
            "Ensure T013a (preprocess.py) has been run successfully."
        )

    def test_load_schema(self):
        """Assert that the schema can be loaded as valid JSON/YAML."""
        # The schema is defined as YAML in the task, but jsonschema expects a dict.
        # We need to parse the YAML content. Since PyYAML might not be in minimal env,
        # we assume the schema was saved as valid JSON or we parse it carefully.
        # The task T004 specified YAML content. We will read it and parse.
        
        # Check if pyyaml is available, otherwise fallback to manual simple parsing if strictly JSON-like
        try:
            import yaml
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            self.assertIsInstance(schema, dict, "Schema must be a valid YAML/JSON object")
        except ImportError:
            # Fallback: Try reading as JSON if YAML import fails, assuming the file might be JSON
            # Or raise a specific error if neither is available but needed.
            # Given the constraints, we assume standard environment for tests.
            # If YAML is not installed, we cannot parse the schema properly without it.
            # However, the task T004 created a YAML file.
            # We will attempt to load as JSON first if YAML fails, or re-raise.
            try:
                with open(self.schema_path, 'r') as f:
                    schema = json.load(f)
                self.assertIsInstance(schema, dict)
            except json.JSONDecodeError:
                self.fail(f"Could not parse schema at {self.schema_path} as JSON or YAML. Ensure pyyaml is installed.")
        
        # Store schema for use in other tests
        self.test_schema = schema

    def test_run_records_conform_to_schema(self):
        """
        Contract test: Validate that run_records.csv rows conform to run_record.schema.yaml.
        This verifies the output of T013a against the contract defined in T004.
        """
        self.assertTrue(hasattr(self, 'test_schema'), "Schema must be loaded first.")
        self.assertTrue(self.data_path.exists(), "Data file must exist.")

        with open(self.data_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            row_count = 0
            errors = []
            
            for row in reader:
                row_count += 1
                # Convert types where necessary for validation
                # The schema expects numbers for run_time_seconds, integers for attempt_number, etc.
                # csv.DictReader reads everything as strings. We must coerce.
                
                validated_row = {}
                for key, value in row.items():
                    if key in self.test_schema.get('properties', {}):
                        prop_schema = self.test_schema['properties'][key]
                        if prop_schema.get('type') == 'number' or prop_schema.get('type') == 'integer':
                            if value == '' or value is None:
                                # Check if required
                                if key in self.test_schema.get('required', []):
                                    errors.append(f"Row {row_count}: Missing required field '{key}'")
                                    continue
                            else:
                                try:
                                    validated_row[key] = float(value)
                                    if prop_schema.get('type') == 'integer':
                                        validated_row[key] = int(validated_row[key])
                                except ValueError:
                                    errors.append(f"Row {row_count}: Invalid number for '{key}': {value}")
                                    continue
                        elif prop_schema.get('type') == 'string':
                            validated_row[key] = str(value) if value else None
                        else:
                            validated_row[key] = value
                    else:
                        validated_row[key] = value

                if errors:
                    continue # Stop at first row error or collect all? Let's collect all.

                try:
                    jsonschema.validate(instance=validated_row, schema=self.test_schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"Row {row_count}: {e.message} (Path: {list(e.path)})")

            if row_count == 0:
                self.fail("No data rows found in run_records.csv to validate.")

            if errors:
                self.fail(f"Validation failed for {len(errors)} rows. Details:\n" + "\n".join(errors[:10])) # Show first 10

    def test_required_fields_present(self):
        """
        Additional check: Ensure all required fields from the schema are present in the CSV header.
        """
        self.assertTrue(self.data_path.exists(), "Data file must exist.")
        
        with open(self.data_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            
            if not headers:
                self.fail("CSV file has no headers.")
            
            # Load schema to get required fields
            try:
                import yaml
                with open(self.schema_path, 'r') as f:
                    schema = yaml.safe_load(f)
            except ImportError:
                with open(self.schema_path, 'r') as f:
                    schema = json.load(f)
            
            required_fields = schema.get('required', [])
            
            missing_fields = [field for field in required_fields if field not in headers]
            
            self.assertEqual(
                len(missing_fields), 0,
                f"Missing required fields in CSV headers: {missing_fields}. "
                f"Expected: {required_fields}, Found: {headers}"
            )

if __name__ == '__main__':
    unittest.main()