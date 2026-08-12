import os
import sys
import unittest
import yaml
from pathlib import Path

# Ensure code directory is in path for relative imports if running as script
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import get_project_root, get_data_dir


def load_schema(schema_path: str = None):
    """
    Loads the dataset schema from the contracts directory.
    If no path is provided, defaults to 'contracts/dataset.schema.yaml'.
    """
    if schema_path is None:
        project_root = get_project_root()
        schema_path = str(project_root / "contracts" / "dataset.schema.yaml")
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_schema_compliance(df, schema):
    """
    Validates that the DataFrame matches the expected schema.
    
    Args:
        df: pandas DataFrame to validate
        schema: dict loaded from schema yaml containing 'columns' definition
    
    Returns:
        bool: True if compliant, False otherwise
    
    Raises:
        AssertionError: If schema is missing required definitions
    """
    if 'columns' not in schema:
        raise AssertionError("Schema must define 'columns'")
    
    expected_columns = set(schema['columns'].keys())
    actual_columns = set(df.columns)
    
    missing_cols = expected_columns - actual_columns
    extra_cols = actual_columns - expected_columns
    
    if missing_cols:
        raise AssertionError(f"Missing required columns: {missing_cols}")
    
    # Check types if defined in schema
    for col_name, col_def in schema['columns'].items():
        if 'dtype' in col_def:
            # Basic type check (simplified for this task)
            # In a full implementation, we would map schema types to numpy/pandas types
            expected_type = col_def['dtype']
            actual_type = str(df[col_name].dtype)
            
            # Allow some flexibility in string representations
            if expected_type == 'string' and 'object' not in actual_type and 'str' not in actual_type:
                raise AssertionError(f"Column '{col_name}' expected type '{expected_type}', got '{actual_type}'")
            elif expected_type == 'float' and 'float' not in actual_type and 'int' not in actual_type:
                raise AssertionError(f"Column '{col_name}' expected type '{expected_type}', got '{actual_type}'")
    
    return True


class TestDataContract(unittest.TestCase):
    """
    Test suite for data contract compliance.
    
    This test is intentionally designed to FAIL initially because the target
    output file 'data/processed/merged_observations.csv' does not exist yet
    (it is produced by later tasks T013b/T014).
    
    The test verifies:
    1. Schema file exists and is loadable.
    2. If the output file exists, it matches the schema.
    3. If the output file is missing, the test fails explicitly to indicate
       that the pipeline prerequisite (T013b) has not been completed.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.schema_path = self.project_root / "contracts" / "dataset.schema.yaml"
        self.output_file = self.project_root / "data" / "processed" / "merged_observations.csv"
        
        # Load schema for use in tests
        try:
            self.schema = load_schema(str(self.schema_path))
        except FileNotFoundError:
            self.schema = None
            self.skipTest("Schema file not found. Cannot run contract tests.")

    def test_schema_compliance(self):
        """
        Test that the merged observations dataset complies with the contract schema.
        
        This test is currently FAILING because the data file has not been generated yet.
        This is expected behavior for the initial implementation of T006a.
        """
        if not self.output_file.exists():
            # Fail loudly to indicate the data generation step is missing
            self.fail(
                f"Data file '{self.output_file}' does not exist. "
                "This test cannot pass until T013b (merge_and_buffer Part B) "
                "has been implemented and executed to generate the merged observations."
            )
        
        import pandas as pd
        df = pd.read_csv(self.output_file)
        
        self.assertIsNotNone(self.schema, "Schema must be loaded to validate compliance")
        
        # This will raise an AssertionError if columns are missing or types mismatch
        validate_schema_compliance(df, self.schema)
        
        # If we reach here, the test passes (but it shouldn't yet due to missing file)
        self.assertTrue(True, "Schema compliance verified")

    def test_schema_structure(self):
        """
        Test that the schema itself has the expected structure.
        """
        self.assertIn('columns', self.schema)
        self.assertIn('species_id', self.schema['columns'])
        self.assertIn('foraging_guild', self.schema['columns'])
        self.assertIn('land_cover_proportions', self.schema['columns'])


if __name__ == '__main__':
    unittest.main()