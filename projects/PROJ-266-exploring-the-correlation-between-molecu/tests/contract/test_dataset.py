"""
Contract tests for the Caco-2 molecular flexibility dataset against dataset.schema.yaml.

These tests validate that the processed dataset conforms to the expected schema,
ensuring data quality and consistency before downstream analysis.
"""

import os
import sys
import yaml
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_project_root


def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def get_processed_data_path() -> Path:
    """
    Locate the processed dataset file.
    Expects data/processed/descriptors.csv or similar.
    """
    data_dir = get_project_root() / "data" / "processed"
    if not data_dir.exists():
        pytest.skip("Processed data directory not found. Run preprocessing/descriptors tasks first.")

    # Look for CSV files in processed directory
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        pytest.skip("No CSV files found in data/processed/. Run descriptor generation tasks first.")

    # Prefer descriptors.csv if it exists, otherwise take the first CSV
    preferred = data_dir / "descriptors.csv"
    if preferred.exists():
        return preferred
    return csv_files[0]


class TestDatasetSchema:
    """Contract tests validating the dataset against the schema."""

    @pytest.fixture
    def schema(self) -> dict:
        """Load the dataset schema."""
        schema_path = get_project_root() / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"
        if not schema_path.exists():
            pytest.fail(f"Schema file not found at {schema_path}. Run T007 first.")
        return load_schema(schema_path)

    @pytest.fixture
    def df(self) -> pd.DataFrame:
        """Load the processed dataset."""
        data_path = get_processed_data_path()
        if not data_path.exists():
            pytest.fail(f"Dataset file not found at {data_path}. Run data processing tasks first.")

        try:
            return pd.read_csv(data_path)
        except Exception as e:
            pytest.fail(f"Failed to load dataset from {data_path}: {e}")

    def test_schema_exists(self, schema):
        """Verify the schema structure is valid."""
        assert "name" in schema, "Schema must have a 'name' field"
        assert "columns" in schema, "Schema must have a 'columns' field"
        assert isinstance(schema["columns"], list), "Columns must be a list"
        assert len(schema["columns"]) > 0, "Schema must define at least one column"

    def test_required_columns_present(self, schema, df):
        """Verify all required columns from schema exist in the dataset."""
        schema_columns = {col["name"] for col in schema["columns"]}
        required_columns = {col["name"] for col in schema["columns"] if col.get("required", False)}

        actual_columns = set(df.columns)

        missing_required = required_columns - actual_columns
        assert not missing_required, f"Missing required columns: {missing_required}"

        # Also check that all schema columns are present (even optional ones)
        missing_all = schema_columns - actual_columns
        if missing_all:
            # Log warning but don't fail if optional columns are missing
            pytest.xfail(f"Optional columns missing from dataset: {missing_all}")

    def test_no_null_required_columns(self, schema, df):
        """Verify required columns have no null values."""
        for col_def in schema["columns"]:
            if col_def.get("required", False):
                col_name = col_def["name"]
                if col_name in df.columns:
                    null_count = df[col_name].isnull().sum()
                    assert null_count == 0, f"Required column '{col_name}' contains {null_count} null values"

    def test_numeric_columns_finite(self, schema, df):
        """Verify numeric columns contain finite values (no NaN, Inf, -Inf)."""
        for col_def in schema["columns"]:
            if col_def.get("type") == "float" and col_def["name"] in df.columns:
                col_name = col_def["name"]
                values = df[col_name].dropna()  # Ignore NaN if not required

                if len(values) > 0:
                    has_inf = np.isinf(values).any()
                    assert not has_inf, f"Column '{col_name}' contains infinite values"

    def test_smiles_format(self, schema, df):
        """Verify SMILES strings are non-empty strings."""
        if "smiles" not in df.columns:
            pytest.skip("SMILES column not present in dataset")

        smiles_series = df["smiles"]
        assert smiles_series.dtype == object or smiles_series.dtype == str, \
            "SMILES column should be string type"

        empty_count = smiles_series.str.len().sum() == 0
        assert not empty_count.any() or (smiles_series == "").sum() == 0, \
            "SMILES column contains empty strings"

    def test_logPapp_range(self, df):
        """Verify logPapp values are within a reasonable physical range."""
        if "logPapp" not in df.columns:
            pytest.skip("logPapp column not present")

        logpapp = df["logPapp"].dropna()
        if len(logpapp) == 0:
            pytest.skip("No logPapp values to validate")

        # Caco-2 logPapp typically ranges from -6 to 6
        # Allow slightly wider range for edge cases
        assert logpapp.min() >= -8, f"logPapp minimum {logpapp.min()} is unreasonably low"
        assert logpapp.max() <= 8, f"logPapp maximum {logpapp.max()} is unreasonably high"

    def test_variance_columns_non_negative(self, df):
        """Verify variance columns are non-negative."""
        variance_cols = ["bond_variance", "angle_variance", "dihedral_variance"]
        for col in variance_cols:
            if col in df.columns:
                values = df[col].dropna()
                if len(values) > 0:
                    assert (values >= 0).all(), f"Column '{col}' contains negative values"

    def test_outlier_flag_boolean(self, df):
        """Verify is_outlier column is boolean if present."""
        if "is_outlier" not in df.columns:
            pytest.skip("is_outlier column not present")

        assert df["is_outlier"].dtype == bool, "is_outlier column must be boolean"

    def test_record_count_minimum(self, df):
        """Verify dataset meets minimum record count for statistical validity."""
        # Per task requirements, we expect >= 500 valid records
        min_records = 500
        assert len(df) >= min_records, \
            f"Dataset has {len(df)} records, expected at least {min_records}"

    def test_schema_metadata_present(self, schema):
        """Verify schema contains required metadata fields."""
        assert "metadata" in schema, "Schema must contain metadata section"
        metadata = schema["metadata"]
        assert "source" in metadata, "Metadata must specify data source"
        assert "retrieval_script" in metadata, "Metadata must specify retrieval script"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])