"""
Contract test for the results/coverage.csv schema.

This test verifies that the output file `results/coverage.csv` exists and
adheres to the strict schema defined in `contracts/output.schema.yaml` (or
the schema logic derived from T019).

Columns expected (per T019):
- series_id
- model
- horizon
- nominal_coverage
- empirical_coverage
- deviation
- p_raw
- p_value
"""

import os
import json
import pytest
import pandas as pd
from pathlib import Path

# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = PROJECT_ROOT / "results" / "coverage.csv"
SCHEMA_FILE = PROJECT_ROOT / "contracts" / "output.schema.yaml"

REQUIRED_COLUMNS = [
    "series_id",
    "model",
    "horizon",
    "nominal_coverage",
    "empirical_coverage",
    "deviation",
    "p_raw",
    "p_value"
]

# Optional: Load schema if it exists to validate types dynamically
# If the schema file is missing, we rely on the REQUIRED_COLUMNS list
# as the contract definition derived from the task description.
def load_schema():
    if not SCHEMA_FILE.exists():
        return None
    try:
        import yaml
        with open(SCHEMA_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def _get_type_validator(schema):
    """Returns a function to validate column types based on schema or defaults."""
    if not schema:
        # Default type expectations based on T019 description
        return {
            "series_id": (str, int),
            "model": str,
            "horizon": (int, float),
            "nominal_coverage": (int, float),
            "empirical_coverage": (int, float),
            "deviation": (int, float),
            "p_raw": (int, float),
            "p_value": (int, float)
        }
    
    # If schema exists, map it (simplified mapping logic)
    # This assumes the schema has a 'properties' or 'columns' section
    type_map = {}
    if "properties" in schema:
        for col, props in schema["properties"].items():
            if "type" in props:
                t = props["type"]
                if t == "number":
                    type_map[col] = (int, float)
                elif t == "integer":
                    type_map[col] = (int, float) # Allow float for int columns in pandas
                elif t == "string":
                    type_map[col] = str
    return type_map

@pytest.fixture(scope="module")
def coverage_data():
    """Fixture to load the coverage.csv file."""
    if not OUTPUT_FILE.exists():
        pytest.fail(f"Output file {OUTPUT_FILE} does not exist. "
                    "The pipeline (T019) must be executed to generate this file.")
    
    try:
        df = pd.read_csv(OUTPUT_FILE)
        return df
    except Exception as e:
        pytest.fail(f"Failed to read {OUTPUT_FILE}: {e}")

def test_file_exists():
    """Contract: The output file must exist."""
    assert OUTPUT_FILE.exists(), f"File {OUTPUT_FILE} not found. Run the pipeline first."

def test_required_columns(coverage_data):
    """Contract: The file must contain all required columns."""
    actual_columns = set(coverage_data.columns)
    missing = set(REQUIRED_COLUMNS) - actual_columns
    extra = actual_columns - set(REQUIRED_COLUMNS)
    
    assert not missing, f"Missing required columns: {missing}"
    
    # Log extra columns if any (non-fatal for this contract, but good for debugging)
    if extra:
        print(f"Warning: Extra columns found: {extra}")

def test_column_types(coverage_data):
    """Contract: Columns must have appropriate data types."""
    schema = load_schema()
    validators = _get_type_validator(schema)
    
    for col, expected_types in validators.items():
        if col not in coverage_data.columns:
            continue # Handled by test_required_columns
        
        # Check if the column is numeric where expected
        if expected_types in [(int, float)]:
            if not pd.api.types.is_numeric_dtype(coverage_data[col]):
                # Allow object columns that can be cast to numeric if they are clearly numbers
                try:
                    pd.to_numeric(coverage_data[col])
                except (ValueError, TypeError):
                    pytest.fail(f"Column '{col}' should be numeric but is not: {coverage_data[col].dtype}")
        
        elif expected_types == str:
            if not pd.api.types.is_string_dtype(coverage_data[col]):
                # Allow object dtype for strings
                if coverage_data[col].dtype != "object":
                    pytest.fail(f"Column '{col}' should be string-like but is {coverage_data[col].dtype}")

def test_no_nulls_in_critical_columns(coverage_data):
    """Contract: Critical columns must not contain null values."""
    critical_cols = ["series_id", "model", "horizon", "nominal_coverage", "empirical_coverage", "p_value"]
    
    for col in critical_cols:
        if col in coverage_data.columns:
            if coverage_data[col].isnull().any():
                count = coverage_data[col].isnull().sum()
                pytest.fail(f"Column '{col}' contains {count} null values.")

def test_coverage_bounds(coverage_data):
    """Contract: Coverage values must be between 0 and 1 (or 0-100 if scaled, but spec implies 0-1)."""
    # Check empirical and nominal coverage
    for col in ["nominal_coverage", "empirical_coverage"]:
        if col in coverage_data.columns:
            # Assuming 0.0 to 1.0 scale based on "0.80", "0.95" in config
            min_val = coverage_data[col].min()
            max_val = coverage_data[col].max()
            
            # Allow slight float precision errors or if data is 0-100 (detect by max > 1)
            if max_val > 1.0 and max_val <= 100.0:
                # Data is likely 0-100 scale, normalize check
                if min_val < 0.0 or max_val > 100.0:
                    pytest.fail(f"Column '{col}' values out of expected range (0-100): [{min_val}, {max_val}]")
            else:
                # Data is 0-1 scale
                if min_val < 0.0 or max_val > 1.0:
                    pytest.fail(f"Column '{col}' values out of expected range (0-1): [{min_val}, {max_val}]")

def test_p_value_bounds(coverage_data):
    """Contract: P-values must be between 0 and 1."""
    if "p_value" in coverage_data.columns:
        min_val = coverage_data["p_value"].min()
        max_val = coverage_data["p_value"].max()
        if min_val < 0.0 or max_val > 1.0:
            pytest.fail(f"P-values out of range [0, 1]: [{min_val}, {max_val}]")
    
    if "p_raw" in coverage_data.columns:
        min_val = coverage_data["p_raw"].min()
        max_val = coverage_data["p_raw"].max()
        if min_val < 0.0 or max_val > 1.0:
            pytest.fail(f"Raw P-values out of range [0, 1]: [{min_val}, {max_val}]")

def test_deviation_calculation(coverage_data):
    """Contract: deviation should be consistent with nominal and empirical coverage."""
    if all(col in coverage_data.columns for col in ["nominal_coverage", "empirical_coverage", "deviation"]):
        # Check if deviation is approximately abs(empirical - nominal)
        # We allow a small tolerance for floating point arithmetic
        calculated_deviation = (coverage_data["nominal_coverage"] - coverage_data["empirical_coverage"]).abs()
        actual_deviation = coverage_data["deviation"].abs()
        
        if not calculated_deviation.equals(actual_deviation):
            # Check if they are close
            if not np.isclose(calculated_deviation, actual_deviation).all():
                pytest.fail("Deviation column does not match |nominal_coverage - empirical_coverage|")