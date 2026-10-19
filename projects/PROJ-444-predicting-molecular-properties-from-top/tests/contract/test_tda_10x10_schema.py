import pandas as pd
import numpy as np
import json
import yaml
import pytest
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parents[2]
TDA_CSV = PROJECT_ROOT / "data" / "processed" / "topological_features_10x10.csv"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-predicting-molecular-properties-from-top"
    / "contracts"
    / "feature_matrix.schema.yaml"
)

def test_file_exists():
    assert TDA_CSV.is_file(), f"TDA feature file missing: {TDA_CSV}"

def test_schema_compliance():
    # Load schema
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)

    # Load CSV
    df = pd.read_csv(TDA_CSV)

    # Required columns
    required = set(schema.get("required", []))
    missing = required - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"

    # Ensure target_property and target_value are present
    assert "target_property" in df.columns
    assert "target_value" in df.columns

    # Verify that there are exactly grid_size^2 feature columns
    grid = 10
    feature_cols = [c for c in df.columns if c.startswith("pixel_")]
    assert len(feature_cols) == grid * grid, (
        f"Expected {grid*grid} feature columns, found {len(feature_cols)}"
    )

def test_no_nan_values():
    df = pd.read_csv(TDA_CSV)
    assert not df.isnull().values.any(), "NaN values found in TDA feature matrix"

def test_image_vector_length():
    df = pd.read_csv(TDA_CSV)
    feature_cols = [c for c in df.columns if c.startswith("pixel_")]
    # All rows must have the same length
    lengths = df[feature_cols].apply(lambda row: len(row.dropna()), axis=1)
    assert lengths.nunique() == 1, "Inconsistent feature vector lengths"

def test_valid_molecules_count():
    # The number of rows should match the filtered ESOL dataset (excluding any invalid SMILES)
    filtered_path = PROJECT_ROOT / "data" / "processed" / "filtered_esol.csv"
    df_filtered = pd.read_csv(filtered_path)
    df_tda = pd.read_csv(TDA_CSV)
    assert df_tda.shape[0] == df_filtered.shape[0], (
        f"Row count mismatch: TDA {df_tda.shape[0]} vs filtered {df_filtered.shape[0]}"
    )