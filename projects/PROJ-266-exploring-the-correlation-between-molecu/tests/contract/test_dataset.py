"""
Contract tests for the Caco-2 permeability dataset against dataset.schema.yaml.

This module validates that the processed dataset (`data/processed/caco2_processed.csv`)
conforms to the schema defined in `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`.

It checks:
1. File existence.
2. Required columns presence.
3. Data types and non-null constraints.
4. Value ranges and formats (e.g., SMILES validity, logPapp range).
5. Record count thresholds.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import yaml
import pytest
from rdkit import Chem
from rdkit.Chem import Descriptors

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, configure_root_logger
from utils.config import get_data_path

# Configure logging
configure_root_logger()
logger = get_logger(__name__)

# Paths
SCHEMA_PATH = project_root / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"
DATASET_PATH = get_data_path() / "processed" / "caco2_processed.csv"

# Constants
MIN_RECORDS = 500
MAX_LOGPAPP = 5.0
MIN_LOGPAPP = -5.0
REQUIRED_COLUMNS = ["smiles", "logPapp", "assay_id", "molecule_id"]


def load_schema() -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def load_dataset() -> pd.DataFrame:
    """Load the processed dataset."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset file not found: {DATASET_PATH}")
    return pd.read_csv(DATASET_PATH)


def validate_smiles(smiles: str) -> bool:
    """Validate if a string is a valid SMILES."""
    if pd.isna(smiles) or not isinstance(smiles, str):
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None


def validate_logPapp(value: float) -> bool:
    """Validate logPapp range."""
    if pd.isna(value):
        return False
    try:
        val = float(value)
        return MIN_LOGPAPP <= val <= MAX_LOGPAPP
    except (ValueError, TypeError):
        return False


class TestDatasetContract:
    """Contract tests for the Caco-2 dataset."""

    @pytest.fixture(scope="class")
    def schema(self):
        return load_schema()

    @pytest.fixture(scope="class")
    def df(self):
        return load_dataset()

    def test_file_exists(self):
        """Contract: Dataset file must exist."""
        assert DATASET_PATH.exists(), f"Dataset file missing: {DATASET_PATH}"

    def test_schema_exists(self):
        """Contract: Schema file must exist."""
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_record_count(self, df):
        """Contract: Dataset must have at least MIN_RECORDS valid records."""
        count = len(df)
        logger.info(f"Dataset contains {count} records. Minimum required: {MIN_RECORDS}")
        assert count >= MIN_RECORDS, f"Dataset has {count} records, expected >= {MIN_RECORDS}"

    def test_required_columns_present(self, df, schema):
        """Contract: All required columns must be present."""
        schema_columns = schema.get("required_columns", [])
        # Fallback to constants if schema doesn't define them explicitly yet
        expected_cols = set(schema_columns) if schema_columns else set(REQUIRED_COLUMNS)
        
        missing = expected_cols - set(df.columns)
        assert not missing, f"Missing required columns: {missing}"

    def test_no_null_smiles(self, df):
        """Contract: SMILES column must not contain nulls."""
        null_count = df["smiles"].isna().sum()
        assert null_count == 0, f"Found {null_count} null values in 'smiles' column"

    def test_no_null_logPapp(self, df):
        """Contract: logPapp column must not contain nulls."""
        null_count = df["logPapp"].isna().sum()
        assert null_count == 0, f"Found {null_count} null values in 'logPapp' column"

    def test_smiles_validity(self, df):
        """Contract: All SMILES strings must be chemically valid."""
        invalid_rows = []
        for idx, row in df.iterrows():
            if not validate_smiles(row["smiles"]):
                invalid_rows.append(idx)
        
        assert not invalid_rows, f"Found {len(invalid_rows)} invalid SMILES entries at indices: {invalid_rows[:10]}..."

    def test_logPapp_range(self, df):
        """Contract: logPapp values must be within physical bounds."""
        invalid_rows = df[~df["logPapp"].apply(validate_logPapp)]
        assert len(invalid_rows) == 0, f"Found {len(invalid_rows)} logPapp values outside range [{MIN_LOGPAPP}, {MAX_LOGPAPP}]"

    def test_assay_id_format(self, df):
        """Contract: Assay IDs should be non-empty strings."""
        # Assuming ChEMBL IDs start with 'CHEMBL' or are numeric strings
        invalid_rows = df[df["assay_id"].isna() | (df["assay_id"] == "")]
        assert len(invalid_rows) == 0, "Found empty or null assay_id entries"

    def test_molecule_id_format(self, df):
        """Contract: Molecule IDs should be non-empty strings."""
        invalid_rows = df[df["molecule_id"].isna() | (df["molecule_id"] == "")]
        assert len(invalid_rows) == 0, "Found empty or null molecule_id entries"

    def test_schema_compliance_summary(self, df, schema):
        """Contract: Full schema compliance check."""
        # This aggregates all checks into a single summary assertion
        errors = []

        # Check columns
        schema_cols = schema.get("required_columns", [])
        if schema_cols and not set(schema_cols).issubset(set(df.columns)):
            errors.append(f"Missing columns: {set(schema_cols) - set(df.columns)}")

        # Check nulls
        for col in ["smiles", "logPapp"]:
            if col in df.columns and df[col].isna().any():
                errors.append(f"Null values in {col}")

        # Check validity
        if "smiles" in df.columns:
            invalid_smiles = ~df["smiles"].apply(validate_smiles)
            if invalid_smiles.any():
                errors.append(f"Invalid SMILES found ({invalid_smiles.sum()} rows)")

        if "logPapp" in df.columns:
            invalid_logp = ~df["logPapp"].apply(validate_logPapp)
            if invalid_logp.any():
                errors.append(f"logPapp out of range ({invalid_logp.sum()} rows)")

        if errors:
            pytest.fail("Schema compliance failed:\n" + "\n".join(errors))

        logger.info("All contract checks passed successfully.")