"""
Contract tests for the feature_matrix schema.

This module validates that the generated feature_matrix.csv adheres to the
schema defined in data/contracts/feature_matrix.schema.yaml. It ensures
that the data integration pipeline (US1) produces output compatible with
the modeling and validation stages.

Tests verify:
1. File existence and readability.
2. Presence of required columns (SNP frequencies, environmental variables, labels).
3. Data types (numeric for features, categorical for metadata).
4. Absence of missing values (imputation complete).
5. Consistency with the schema definition (min/max values, allowed categories).
"""

import os
import sys
import json
import csv
import math
from pathlib import Path
from typing import Dict, List, Any, Set

import pytest
import numpy as np

# Project root handling for execution context
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CONTRACTS_DIR = DATA_DIR / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "feature_matrix.schema.yaml"
FEATURE_MATRIX_PATH = PROCESSED_DIR / "feature_matrix.csv"

# Expected columns based on US1 design (SNP freq + Env + Label)
# Note: Actual column names may vary slightly by species, but structure must hold.
REQUIRED_BASE_COLUMNS = {
    "sample_id",
    "species",
    "disease_status",  # Target label
    "latitude",
    "longitude",
}

# Environmental variables expected from ERA5/NOAA integration
ENV_COLUMNS = {
    "temp_mean",
    "temp_max",
    "temp_min",
    "humidity_mean",
    "precipitation_total",
}

# SNP columns are dynamic per species, but must follow pattern:
# species_snps -> list of SNP IDs or generic "snp_0", "snp_1" if aggregated
# We check for the presence of *at least one* SNP column if species is present.
SNP_COLUMN_PREFIX = "snp_"


def load_schema() -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not SCHEMA_PATH.exists():
        # If schema file is missing, we cannot validate against it.
        # In a real CI, this might be a failure, but for this test,
        # we assert the file exists first.
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    # Simple YAML parser for the expected structure (no external deps if possible)
    # Since tasks.md mentions pyyaml in requirements, we try to import it.
    try:
        import yaml
        with open(SCHEMA_PATH, "r") as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: manual parsing if yaml is not installed (unlikely given requirements)
        # But we assume requirements.txt (T002a) includes pyyaml.
        raise RuntimeError("PyYAML is required to load schema. Install via requirements.txt.")


def load_feature_matrix() -> List[Dict[str, str]]:
    """Load the feature matrix CSV as a list of dictionaries."""
    if not FEATURE_MATRIX_PATH.exists():
        raise FileNotFoundError(
            f"Feature matrix not found at {FEATURE_MATRIX_PATH}. "
            "Run the data ingestion pipeline (US1) first."
        )

    with open(FEATURE_MATRIX_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


class TestFeatureMatrixSchema:
    """Contract tests for feature_matrix.csv."""

    @pytest.fixture(scope="class")
    def schema(self) -> Dict[str, Any]:
        """Load the schema once for the test class."""
        return load_schema()

    @pytest.fixture(scope="class")
    def data(self) -> List[Dict[str, str]]:
        """Load the data once for the test class."""
        return load_feature_matrix()

    def test_file_exists(self):
        """Assert that the feature_matrix.csv file exists."""
        assert FEATURE_MATRIX_PATH.exists(), f"File missing: {FEATURE_MATRIX_PATH}"

    def test_schema_file_exists(self):
        """Assert that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_required_columns_present(self, data, schema):
        """Assert that all required base columns are present."""
        if not data:
            pytest.skip("No data rows to check.")

        headers = set(data[0].keys())
        missing = REQUIRED_BASE_COLUMNS - headers
        assert not missing, f"Missing required columns: {missing}"

    def test_no_missing_values(self, data):
        """Assert that there are no empty strings or NaNs in the dataset."""
        if not data:
            pytest.skip("No data rows to check.")

        for i, row in enumerate(data):
            for key, value in row.items():
                if value is None or value == "":
                    pytest.fail(f"Row {i}, Column '{key}' contains a missing value.")
                # Check for string representations of NaN
                if isinstance(value, str) and value.lower() in ["nan", "na", "n/a", "null"]:
                    pytest.fail(f"Row {i}, Column '{key}' contains a NaN placeholder: '{value}'")

    def test_numeric_columns_are_valid(self, data):
        """Assert that columns expected to be numeric are parseable as floats."""
        if not data:
            pytest.skip("No data rows to check.")

        numeric_candidates = set(data[0].keys()) - REQUIRED_BASE_COLUMNS
        # Exclude species and status which are categorical
        numeric_candidates.discard("species")
        numeric_candidates.discard("disease_status")

        for i, row in enumerate(data):
            for col in numeric_candidates:
                val = row.get(col)
                if val is None:
                    continue
                try:
                    float(val)
                except ValueError:
                    pytest.fail(
                        f"Row {i}, Column '{col}' is not numeric: '{val}' "
                        f"(Expected float, got string)"
                    )

    def test_species_in_whitelist(self, data, schema):
        """Assert that species values match the allowed list in schema or config."""
        if not data:
            pytest.skip("No data rows to check.")

        # Try to get allowed species from schema, fallback to config
        allowed_species = None
        if "properties" in schema and "species" in schema["properties"]:
            prop = schema["properties"]["species"]
            if "enum" in prop:
                allowed_species = set(prop["enum"])

        if not allowed_species:
            # Fallback to known species from config if schema doesn't specify
            from src.utils.config import get_species_info
            allowed_species = set(get_species_info().keys())

        for i, row in enumerate(data):
            species = row.get("species")
            if species and species not in allowed_species:
                pytest.fail(
                    f"Row {i}: Unknown species '{species}'. "
                    f"Allowed: {allowed_species}"
                )

    def test_disease_status_valid(self, data, schema):
        """Assert that disease_status is a valid categorical value."""
        if not data:
            pytest.skip("No data rows to check.")

        allowed_statuses = {"susceptible", "resistant", "infected", "healthy"}
        if "properties" in schema and "disease_status" in schema["properties"]:
            prop = schema["properties"]["disease_status"]
            if "enum" in prop:
                allowed_statuses = set(prop["enum"])

        for i, row in enumerate(data):
            status = row.get("disease_status", "").lower()
            if status and status not in allowed_statuses:
                pytest.fail(
                    f"Row {i}: Invalid disease_status '{row['disease_status']}'. "
                    f"Allowed: {allowed_statuses}"
                )

    def test_at_least_one_snp_column(self, data):
        """Assert that at least one SNP column exists (dynamic columns)."""
        if not data:
            pytest.skip("No data rows to check.")

        headers = set(data[0].keys())
        snp_cols = [h for h in headers if h.startswith(SNP_COLUMN_PREFIX) or "snp" in h.lower()]
        assert len(snp_cols) > 0, (
            "No SNP columns found in feature matrix. "
            "The genomic data integration step may have failed or produced no variants."
        )

    def test_schema_compliance(self, data, schema):
        """
        Perform a basic structural check against the schema definition.
        Checks min/max constraints if defined.
        """
        if not data:
            pytest.skip("No data rows to check.")

        properties = schema.get("properties", {})

        for row_idx, row in enumerate(data):
            for col_name, value in row.items():
                if col_name not in properties:
                    continue

                prop_def = properties[col_name]

                # Check type constraints
                if prop_def.get("type") == "number":
                    try:
                        num_val = float(value)
                        if "minimum" in prop_def and num_val < prop_def["minimum"]:
                            pytest.fail(
                                f"Row {row_idx}, Col {col_name}: Value {num_val} "
                                f"is below minimum {prop_def['minimum']}"
                            )
                        if "maximum" in prop_def and num_val > prop_def["maximum"]:
                            pytest.fail(
                                f"Row {row_idx}, Col {col_name}: Value {num_val} "
                                f"is above maximum {prop_def['maximum']}"
                            )
                    except ValueError:
                        # Handled in numeric test, but double check here
                        pass

    def test_zero_missing_values_in_env_data(self, data):
        """Specific check for environmental data completeness (k-NN imputation result)."""
        if not data:
            pytest.skip("No data rows to check.")

        env_cols = [c for c in data[0].keys() if c in ENV_COLUMNS]
        if not env_cols:
            pytest.skip("Environmental columns not found in dataset.")

        for i, row in enumerate(data):
            for col in env_cols:
                val = row.get(col)
                if val is None or val == "":
                    pytest.fail(
                        f"Environmental data missing for {col} in row {i}. "
                        "Imputation (k-NN) should have filled this."
                    )