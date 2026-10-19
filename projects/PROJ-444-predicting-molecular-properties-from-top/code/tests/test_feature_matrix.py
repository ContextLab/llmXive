"""
Feature-matrix contract test (Task T003).

Loads ``data/processed/topological_features_10x10.csv`` and validates it
against ``specs/001-predicting-molecular-properties-from-top/contracts/
feature_matrix.schema.yaml``, ensuring ``target_property`` and
``target_value`` are present. Both ``molecule_id`` columns are cast to
``str`` before any merge with ``filtered_esol.csv``.
"""

import json

import jsonschema
import pandas as pd
import pytest
import yaml
from pathlib import Path

SCHEMA_PATH = Path(
    "specs/001-predicting-molecular-properties-from-top/contracts/"
    "feature_matrix.schema.yaml"
)
FEATURES_PATH = Path("data/processed/topological_features_10x10.csv")
DATASET_PATH = Path("data/processed/filtered_esol.csv")

N_PIXELS = 100  # 10 x 10 persistence image (FR-002)


def _load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file missing: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), "Schema must be a mapping"
    return schema


def _load_features() -> pd.DataFrame:
    if not FEATURES_PATH.exists():
        pytest.fail(
            f"TDA features file missing: {FEATURES_PATH}. "
            "Run code/02_tda_computation.py --grid 10 first."
        )
    # molecule_id MUST be loaded as string (type-safe merges).
    return pd.read_csv(FEATURES_PATH, dtype={"molecule_id": str})


def _load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        pytest.fail(f"Filtered dataset file missing: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH, dtype={"molecule_id": str})
    if "molecule_id" not in df.columns:
        df["molecule_id"] = df.index.astype(str)
    # Cast to str explicitly before any merge (plan: type safety).
    df["molecule_id"] = df["molecule_id"].astype(str)
    return df


def _pixel_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c.startswith("pixel_")]


def _build_record(row, pixel_cols: list) -> dict:
    """Construct the schema record for one row of the feature matrix."""
    if "features" in row.index and isinstance(row["features"], str):
        features = [float(v) for v in json.loads(row["features"])]
    else:
        features = [float(row[c]) for c in pixel_cols]

    if "feature_names" in row.index and isinstance(row["feature_names"], str):
        feature_names = list(json.loads(row["feature_names"]))
    else:
        feature_names = list(pixel_cols)

    if "target_value" in row.index and pd.notna(row["target_value"]):
        target_value = float(row["target_value"])
    else:
        target_value = float(row["logP"])

    target_property = (
        str(row["target_property"])
        if "target_property" in row.index
        and pd.notna(row["target_property"])
        else "logP"
    )

    return {
        "molecule_id": str(row["molecule_id"]),
        "features": features,
        "feature_names": feature_names,
        "target_property": target_property,
        "target_value": target_value,
    }


def test_feature_matrix_schema():
    """Validate feature-matrix records against feature_matrix.schema.yaml."""
    schema = _load_schema()
    df_features = _load_features()
    df_dataset = _load_dataset()

    # Cast BOTH molecule_id columns to str before merging.
    df_features["molecule_id"] = df_features["molecule_id"].astype(str)
    df_dataset["molecule_id"] = df_dataset["molecule_id"].astype(str)

    df_merged = pd.merge(df_features, df_dataset, on="molecule_id")
    assert not df_merged.empty, (
        "Merged feature matrix is empty; check that molecule_ids match."
    )

    pixel_cols = _pixel_columns(df_features)
    assert len(pixel_cols) == N_PIXELS, (
        f"Expected {N_PIXELS} pixel columns, found {len(pixel_cols)}"
    )

    # Validate a representative sample of records against the contract.
    for _, row in df_merged.head(100).iterrows():
        record = _build_record(row, pixel_cols)
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.ValidationError as e:
            pytest.fail(
                f"Schema validation failed for molecule "
                f"{record['molecule_id']}: {e.message}"
              )
        except jsonschema.SchemaError as e:
            pytest.fail(f"The schema itself is invalid: {e.message}")

def test_feature_matrix_dimensions():
    """FR-002: 10x10 = 100 pixel features, plus id and target fields."""
    df = _load_features()

    assert "molecule_id" in df.columns, "Missing 'molecule_id' column"
    assert "target_property" in df.columns, (
        "Missing 'target_property' column (required by "
        "feature_matrix.schema.yaml)"
    )
    assert "target_value" in df.columns, (
        "Missing 'target_value' column (required by "
        "feature_matrix.schema.yaml)"
    )

    pixel_cols = _pixel_columns(df)
    assert len(pixel_cols) == N_PIXELS, (
        f"Expected {N_PIXELS} pixel columns, found {len(pixel_cols)}"
    )
    assert all(f"pixel_{i}" in df.columns for i in range(N_PIXELS)), (
        "Pixel columns pixel_0..pixel_99 must all be present"
    )

    # molecule_id must be string-typed (type-safe merge requirement).
    assert df["molecule_id"].dtype == object, (
        "molecule_id must be loaded as a string column"
    )
    assert df["molecule_id"].map(lambda v: isinstance(v, str)).all(), (
        "All molecule_id values must be strings"
    )

    # Every feature row must pair with a row in the filtered dataset.
    df_dataset = _load_dataset()
    df_features = df.copy()
    df_features["molecule_id"] = df_features["molecule_id"].astype(str)
    df_merged = pd.merge(df_features, df_dataset, on="molecule_id")
    assert len(df_merged) == len(df_features), (
        f"Row-count mismatch after merge: features={len(df_features)}, "
        f"merged={len(df_merged)}"
    )

def test_feature_matrix_no_nans():
    """T002 requirement: no NaN values in the feature matrix."""
    df = _load_features()
    pixel_cols = _pixel_columns(df)
    assert pixel_cols, "No pixel columns found in the feature matrix"
    assert not df[pixel_cols].isnull().any().any(), (
        "Feature matrix contains NaN values"
    )
    # Target fields must also be populated (no hollow results).
    assert not df["target_value"].isnull().any(), (
        "target_value contains NaN values"
    )
    assert df["target_property"].notna().all() and (
        df["target_property"].astype(str).str.len() > 0
    ).all(), "target_property must be populated for every row"