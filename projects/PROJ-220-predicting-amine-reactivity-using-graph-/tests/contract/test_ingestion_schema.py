"""
Contract test for data ingestion schema (T012).

Verifies that the data ingestion pipeline produces records conforming to the
expected schema defined in the project specifications (US1).

This test ensures:
1. All required fields are present in every record.
2. Data types match the specification (e.g., SMILES is string, kinetics are float).
3. No NaN values exist in critical columns (SMILES, normalized_rate, pKa).
4. SMILES strings are valid (can be parsed by RDKit).

Note: This test expects the ingestion pipeline (T014, T015) to have been run
and produced the output file at `data/derived/ingested_reactions.csv`.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd
import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "derived"
OUTPUT_FILE = DATA_DIR / "ingested_reactions.csv"

# Required schema definition based on US1 and T014/T015 specs
# Fields: SMILES, normalized_rate, pKa, reaction_id, source, temperature_K, ea_kj_mol (optional),
#         atom_count, bond_count, graph_nodes, graph_edges
REQUIRED_FIELDS: Set[str] = {
    "smiles",
    "normalized_rate",
    "pka",
    "reaction_id",
    "source",
    "temperature_k",
}

OPTIONAL_FIELDS: Set[str] = {
    "ea_kj_mol",
    "atom_count",
    "bond_count",
    "graph_nodes",
    "graph_edges",
}

STRING_FIELDS: Set[str] = {"smiles", "reaction_id", "source"}
FLOAT_FIELDS: Set[str] = {"normalized_rate", "pka", "temperature_k", "ea_kj_mol"}
INT_FIELDS: Set[str] = {"atom_count", "bond_count"}

NON_NULL_FIELDS: Set[str] = {"smiles", "normalized_rate", "pka", "reaction_id"}

# Minimum number of records expected for a valid ingestion run
MIN_RECORDS = 10


def _load_ingestion_output() -> pd.DataFrame:
    """Load the ingestion output CSV. Fails loudly if file is missing."""
    if not OUTPUT_FILE.exists():
        pytest.fail(
            f"Ingestion output file not found at {OUTPUT_FILE}. "
            "Please run the ingestion pipeline (T014/T015) before running this contract test."
        )
    
    try:
        df = pd.read_csv(OUTPUT_FILE)
    except Exception as e:
        pytest.fail(f"Failed to read ingestion output CSV: {e}")
    
    if df.empty:
        pytest.fail("Ingestion output CSV is empty. No records were ingested.")
    
    return df


def _validate_smiles(smiles: str) -> bool:
    """Validate that a SMILES string is parsable by RDKit."""
    if not isinstance(smiles, str) or pd.isna(smiles):
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None


def test_ingestion_schema_exists_and_has_records():
    """Test that the ingestion output file exists and contains data."""
    df = _load_ingestion_output()
    assert len(df) >= MIN_RECORDS, (
        f"Ingestion output has fewer than {MIN_RECORDS} records ({len(df)}). "
        "This suggests the ingestion pipeline failed to fetch sufficient data."
    )


def test_ingestion_schema_has_required_columns():
    """Test that all required columns are present in the output."""
    df = _load_ingestion_output()
    missing = REQUIRED_FIELDS - set(df.columns)
    assert not missing, f"Missing required columns in ingestion output: {missing}"


def test_ingestion_schema_data_types():
    """Test that columns have the correct data types."""
    df = _load_ingestion_output()
    
    for col in STRING_FIELDS:
        if col in df.columns:
            # Allow object type which covers string in pandas
            assert df[col].dtype == object or df[col].dtype.name == "string", (
                f"Column '{col}' should be string, got {df[col].dtype}"
            )
    
    for col in FLOAT_FIELDS:
        if col in df.columns:
            assert pd.api.types.is_float_dtype(df[col]), (
                f"Column '{col}' should be float, got {df[col].dtype}"
            )
    
    for col in INT_FIELDS:
        if col in df.columns:
            assert pd.api.types.is_integer_dtype(df[col]), (
                f"Column '{col}' should be integer, got {df[col].dtype}"
            )


def test_ingestion_schema_no_null_required_fields():
    """Test that critical fields have no missing values."""
    df = _load_ingestion_output()
    
    for col in NON_NULL_FIELDS:
        if col in df.columns:
            null_count = df[col].isna().sum()
            assert null_count == 0, (
                f"Column '{col}' contains {null_count} missing values. "
                "Critical fields must not be null."
            )


def test_ingestion_schema_valid_smiles():
    """Test that all SMILES strings are valid chemical structures."""
    df = _load_ingestion_output()
    
    invalid_smiles = []
    for idx, smiles in enumerate(df["smiles"]):
        if not _validate_smiles(smiles):
            invalid_smiles.append((idx, smiles))
    
    assert not invalid_smiles, (
        f"Found {len(invalid_smiles)} invalid SMILES strings:\n"
        + "\n".join([f"  Row {idx}: {s}" for idx, s in invalid_smiles[:5]])
    )


def test_ingestion_schema_kinetics_range():
    """Test that normalized rate values are within reasonable bounds."""
    df = _load_ingestion_output()
    
    # Log(rate) typically ranges from -10 to 10 for most chemical reactions
    # Normalized rate (if not log) should be positive
    # We assume normalized_rate is log(rate) based on T015 description
    if "normalized_rate" in df.columns:
        rates = df["normalized_rate"]
        # Check for extreme outliers that might indicate normalization errors
        # Allow a wide range but catch obvious errors (e.g., -1000 or 1000)
        assert rates.min() > -100, f"normalized_rate minimum {rates.min()} is suspiciously low"
        assert rates.max() < 100, f"normalized_rate maximum {rates.max()} is suspiciously high"


def test_ingestion_schema_pka_range():
    """Test that pKa values are within chemical reality bounds."""
    df = _load_ingestion_output()
    
    if "pka" in df.columns:
        pka_values = df["pka"]
        # pKa for amines typically ranges from 0 to 14, but we allow -5 to 20 for edge cases
        assert pka_values.min() >= -5, f"pKa minimum {pka_values.min()} is chemically impossible"
        assert pka_values.max() <= 20, f"pKa maximum {pka_values.max()} is chemically impossible"