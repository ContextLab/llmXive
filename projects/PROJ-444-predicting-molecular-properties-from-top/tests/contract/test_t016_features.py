"""
Contract Test for Task T016: Feature Generation.

Verifies:
1. Output files exist.
2. Schema compliance (required columns present).
3. No null values in feature columns.
4. Consistency between TDA and Traditional datasets (same SMILES count).
"""
import os
import sys
import pytest
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

TDA_FEATURES_PATH = project_root / "data" / "processed" / "tda_features.csv"
TRAD_FEATURES_PATH = project_root / "data" / "processed" / "traditional_descriptors.csv"

# Expected columns for traditional descriptors (defined in 01_generate_features.py)
EXPECTED_TRAD_COLS = {
    'smiles', 'MolWt', 'MolLogP', 'TPSA', 'NumHDonors', 'NumHAcceptors',
    'NumRotatableBonds', 'NumAromaticRings', 'NumAliphaticRings', 'NumHeteroatoms',
    'FractionCSP3', 'HeavyAtomCount', 'RingCount'
}

def test_tda_features_file_exists():
    """Verify TDA features file exists."""
    assert TDA_FEATURES_PATH.exists(), f"File not found: {TDA_FEATURES_PATH}"

def test_traditional_descriptors_file_exists():
    """Verify Traditional descriptors file exists."""
    assert TRAD_FEATURES_PATH.exists(), f"File not found: {TRAD_FEATURES_PATH}"

def test_tda_features_schema():
    """Verify TDA features file has required columns (smiles + persistence image cols)."""
    if not TDA_FEATURES_PATH.exists():
        pytest.skip("TDA features file missing.")
    
    df = pd.read_csv(TDA_FEATURES_PATH)
    assert 'smiles' in df.columns, "Missing 'smiles' column in TDA features."
    # Check for at least one persistence image column (pattern: pixel_*)
    pixel_cols = [c for c in df.columns if c.startswith('pixel_')]
    assert len(pixel_cols) > 0, "No persistence image columns found in TDA features."

def test_traditional_descriptors_schema():
    """Verify Traditional descriptors file has all expected descriptor columns."""
    if not TRAD_FEATURES_PATH.exists():
        pytest.skip("Traditional descriptors file missing.")
    
    df = pd.read_csv(TRAD_FEATURES_PATH)
    actual_cols = set(df.columns)
    missing_cols = EXPECTED_TRAD_COLS - actual_cols
    assert len(missing_cols) == 0, f"Missing columns in traditional descriptors: {missing_cols}"

def test_no_null_values_tda():
    """Verify no null values in TDA feature columns."""
    if not TDA_FEATURES_PATH.exists():
        pytest.skip("TDA features file missing.")
    
    df = pd.read_csv(TDA_FEATURES_PATH)
    feature_cols = [c for c in df.columns if c != 'smiles']
    null_counts = df[feature_cols].isnull().sum()
    assert null_counts.sum() == 0, f"Found null values in TDA features:\n{null_counts[null_counts > 0]}"

def test_no_null_values_trad():
    """Verify no null values in Traditional descriptor columns."""
    if not TRAD_FEATURES_PATH.exists():
        pytest.skip("Traditional descriptors file missing.")
    
    df = pd.read_csv(TRAD_FEATURES_PATH)
    feature_cols = [c for c in df.columns if c != 'smiles']
    null_counts = df[feature_cols].isnull().sum()
    assert null_counts.sum() == 0, f"Found null values in Traditional descriptors:\n{null_counts[null_counts > 0]}"

def test_consistent_molecule_count():
    """Verify both datasets have the same number of molecules (same SMILES)."""
    if not TDA_FEATURES_PATH.exists() or not TRAD_FEATURES_PATH.exists():
        pytest.skip("One or both files missing.")
    
    df_tda = pd.read_csv(TDA_FEATURES_PATH)
    df_trad = pd.read_csv(TRAD_FEATURES_PATH)
    
    assert len(df_tda) == len(df_trad), \
        f"Molecule count mismatch: TDA={len(df_tda)}, Trad={len(df_trad)}"
    
    # Verify SMILES sets match
    smiles_tda = set(df_tda['smiles'])
    smiles_trad = set(df_trad['smiles'])
    assert smiles_tda == smiles_trad, "SMILES sets do not match between TDA and Traditional datasets."

def test_non_empty_datasets():
    """Verify datasets are not empty."""
    if not TDA_FEATURES_PATH.exists():
        pytest.skip("TDA features file missing.")
    
    df_tda = pd.read_csv(TDA_FEATURES_PATH)
    assert len(df_tda) > 0, "TDA features dataset is empty."
    
    if not TRAD_FEATURES_PATH.exists():
        pytest.skip("Traditional descriptors file missing.")
    
    df_trad = pd.read_csv(TRAD_FEATURES_PATH)
    assert len(df_trad) > 0, "Traditional descriptors dataset is empty."
