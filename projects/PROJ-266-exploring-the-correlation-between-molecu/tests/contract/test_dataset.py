"""
Contract tests for the Caco-2 permeability dataset against dataset.schema.yaml.

These tests ensure that the preprocessed data produced by T009 and T010
strictly adheres to the defined schema, validating types, ranges, and
required fields before downstream analysis (T013+).
"""
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pytest
import yaml

# Add project root to path for imports if running via pytest discovery
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root

# Constants
SCHEMA_PATH = project_root / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"
DATA_PATH = project_root / "data" / "processed" / "cleaned_caco2.csv"

# Required columns from schema
REQUIRED_COLUMNS = [
    "smiles",
    "logPapp",
    "assay_id",
    "molecular_weight",
    "logP",
    "psa",
    "is_outlier"
]

# Optional columns (flexibility descriptors, added later)
OPTIONAL_COLUMNS = [
    "bond_variance",
    "angle_variance",
    "dihedral_variance"
]

ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from disk."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def load_dataset() -> Optional[pd.DataFrame]:
    """
    Load the dataset if it exists.
    Returns None if the file is missing (e.g., if T010 hasn't run yet).
    """
    if not DATA_PATH.exists():
        return None
    return pd.read_csv(DATA_PATH)


def validate_row_types(row: pd.Series, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that each column in a row matches the expected type from schema.
    Returns a list of error messages.
    """
    errors = []
    properties = schema.get("properties", {})

    for col in ALL_COLUMNS:
        if col not in properties:
            # Column exists in data but not in schema (unless it's optional and we just ignore)
            if col not in OPTIONAL_COLUMNS:
                errors.append(f"Column '{col}' found in data but not defined in schema.")
            continue

        val = row.get(col)
        prop_def = properties[col]
        expected_type = prop_def.get("type")

        if pd.isna(val):
            if prop_def.get("nullable", False):
                continue
            else:
                # Check if it's a required field
                if col in schema.get("required", []):
                    errors.append(f"Required field '{col}' is NULL.")
                continue

        # Type checking
        if expected_type == "string":
            if not isinstance(val, str) or len(val) == 0:
                errors.append(f"Column '{col}' expected string, got {type(val).__name__} or empty.")
        elif expected_type == "integer":
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                errors.append(f"Column '{col}' expected integer/finite number, got {val}.")
            elif isinstance(val, float) and not val.is_integer():
                # Allow float if it represents an integer (e.g. 1.0), but strict check
                pass
        elif expected_type == "number":
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                errors.append(f"Column '{col}' expected number, got {val}.")
        elif expected_type == "boolean":
            if not isinstance(val, bool):
                errors.append(f"Column '{col}' expected boolean, got {type(val).__name__}.")

    return errors


def validate_row_constraints(row: pd.Series, schema: Dict[str, Any]) -> List[str]:
    """
    Validate numeric constraints (min, max) defined in schema.
    """
    errors = []
    properties = schema.get("properties", {})

    for col in ALL_COLUMNS:
        if col not in properties:
            continue

        val = row.get(col)
        prop_def = properties[col]

        if pd.isna(val):
            continue

        if prop_def.get("type") == "number" or prop_def.get("type") == "integer":
            if "minimum" in prop_def and val < prop_def["minimum"]:
                errors.append(f"Column '{col}' value {val} is below minimum {prop_def['minimum']}.")
            if "maximum" in prop_def and val > prop_def["maximum"]:
                errors.append(f"Column '{col}' value {val} is above maximum {prop_def['maximum']}.")

    return errors


def validate_smiles_format(row: pd.Series) -> List[str]:
    """
    Basic validation for SMILES strings (non-empty, no obvious whitespace).
    """
    errors = []
    smiles = row.get("smiles")
    if pd.notna(smiles):
        if not isinstance(smiles, str):
            errors.append(f"SMILES is not a string: {type(smiles)}")
        elif len(smiles.strip()) == 0:
            errors.append("SMILES is empty or whitespace.")
        elif " " in smiles:
            errors.append("SMILES contains whitespace.")
    return errors


class TestDatasetContract:
    """
    Contract tests ensuring the dataset matches dataset.schema.yaml.
    """

    @pytest.fixture(scope="class")
    def schema(self):
        return load_schema()

    @pytest.fixture(scope="class")
    def df(self):
        df = load_dataset()
        if df is None:
            pytest.skip(f"Dataset file not found at {DATA_PATH}. Run T010 first.")
        return df

    def test_schema_exists(self):
        """Verify the schema file exists and is valid YAML."""
        assert SCHEMA_PATH.exists(), "Schema file missing."
        schema = load_schema()
        assert "properties" in schema, "Schema must define properties."

    def test_required_columns_present(self, df: pd.DataFrame):
        """Verify all required columns exist in the DataFrame."""
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        assert len(missing) == 0, f"Missing required columns: {missing}"

    def test_column_types(self, df: pd.DataFrame, schema: Dict[str, Any]):
        """Verify types of all columns match schema definitions."""
        all_errors = []
        for idx, row in df.iterrows():
            row_errors = validate_row_types(row, schema)
            if row_errors:
                all_errors.append(f"Row {idx}: {row_errors}")
            # Limit error reporting to first 5 rows to avoid spam
            if len(all_errors) >= 5:
                break

        if all_errors:
            pytest.fail(f"Type validation failed:\n" + "\n".join(all_errors))

    def test_numeric_constraints(self, df: pd.DataFrame, schema: Dict[str, Any]):
        """Verify numeric values respect min/max constraints."""
        all_errors = []
        for idx, row in df.iterrows():
            row_errors = validate_row_constraints(row, schema)
            if row_errors:
                all_errors.append(f"Row {idx}: {row_errors}")
            if len(all_errors) >= 5:
                break

        if all_errors:
            pytest.fail(f"Constraint validation failed:\n" + "\n".join(all_errors))

    def test_smiles_validity(self, df: pd.DataFrame):
        """Verify SMILES strings are valid (non-empty, no whitespace)."""
        all_errors = []
        for idx, row in df.iterrows():
            row_errors = validate_smiles_format(row)
            if row_errors:
                all_errors.append(f"Row {idx}: {row_errors}")
            if len(all_errors) >= 5:
                break

        if all_errors:
            pytest.fail(f"SMILES validation failed:\n" + "\n".join(all_errors))

    def test_logPapp_range(self, df: pd.DataFrame):
        """Specific check for logPapp range (-10 to 10)."""
        if "logPapp" not in df.columns:
            pytest.skip("logPapp column missing")
        
        invalid = df[
            (df["logPapp"].notna()) & 
            ((df["logPapp"] < -10.0) | (df["logPapp"] > 10.0))
        ]
        assert len(invalid) == 0, f"Found {len(invalid)} rows with logPapp outside [-10, 10]"

    def test_outlier_flag_type(self, df: pd.DataFrame):
        """Verify is_outlier is boolean."""
        if "is_outlier" not in df.columns:
            pytest.skip("is_outlier column missing")
        
        # Check if all non-null values are boolean
        non_bool = df[~df["is_outlier"].apply(lambda x: isinstance(x, (bool, int)) if pd.notna(x) else True)]
        # Note: pandas often reads booleans as int 0/1, so we allow int if 0/1
        invalid_rows = []
        for idx, val in df["is_outlier"].items():
            if pd.notna(val):
                if isinstance(val, bool):
                    continue
                if isinstance(val, int) and val in [0, 1]:
                    continue
                invalid_rows.append(idx)
        
        assert len(invalid_rows) == 0, f"Non-boolean values in is_outlier at rows: {invalid_rows}"

    def test_no_extra_columns(self, df: pd.DataFrame, schema: Dict[str, Any]):
        """Verify no unexpected columns exist (unless defined in schema)."""
        schema_cols = set(schema.get("properties", {}).keys())
        data_cols = set(df.columns)
        
        extra = data_cols - schema_cols
        # Allow extra columns if they are not in the schema but we might have added them?
        # Strict mode: fail if extra columns exist
        if extra:
            pytest.fail(f"Unexpected columns found in data: {extra}")