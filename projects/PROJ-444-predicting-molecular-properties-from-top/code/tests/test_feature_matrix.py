import pytest
import pandas as pd
import yaml
import jsonschema
from pathlib import Path

def test_feature_matrix_schema():
    """
    Validates that the TDA feature matrix (persistence_images_10x10.csv) 
    conforms to the contract defined in feature_matrix.schema.yaml.
    
    Since the schema describes a single record object, we merge the feature CSV 
    with the target values from filtered_esol.csv and validate that 
    the resulting records match the schema.
    """
    # Define paths
    schema_path = Path("specs/001-predicting-molecular-properties-from-top/contracts/feature_matrix.schema.yaml")
    features_path = Path("data/processed/persistence_images_10x10.csv")
    dataset_path = Path("data/processed/filtered_esol.csv")

    # 1. Load Schema
    if not schema_path.exists():
        pytest.fail(f"Schema file missing: {schema_path}")
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    # 2. Load Data
    if not features_path.exists():
        pytest.fail(f"TDA features file missing: {features_path}")
    if not dataset_path.exists():
        pytest.fail(f"Filtered dataset file missing: {dataset_path}")

    df_features = pd.read_csv(features_path)
    df_dataset = pd.read_csv(dataset_path)

    # Ensure molecule_id exists in both for merging.
    # 02_tda_computation.py generates molecule_id based on index if missing.
    if "molecule_id" not in df_dataset.columns:
        df_dataset["molecule_id"] = df_dataset.index.astype(str)
    
    # Merge feature matrix with target values (logP)
    df_merged = pd.merge(df_features, df_dataset, on="molecule_id")
    
    assert not df_merged.empty, "Merged feature matrix is empty; check if molecule_ids match."

    # 3. Validate records against schema
    # We validate a representative sample (first 100 rows) to ensure compliance
    pixel_cols = [c for c in df_features.columns if c.startswith("pixel_")]
    assert len(pixel_cols) == 100, f"Expected 100 pixels for 10x10 resolution, found {len(pixel_cols)}"

    for _, row in df_merged.head(100).iterrows():
        # Construct the object exactly as defined in the YAML schema
        record = {
            "molecule_id": str(row["molecule_id"]),
            "features": [float(row[c]) for c in pixel_cols],
            "feature_names": pixel_cols,
            "target_property": "logP",
            "target_value": float(row["logP"])
        }
        
        # Use jsonschema to validate the constructed record against the contract
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Schema validation failed for molecule {record['molecule_id']}: {e.message}")
        except jsonschema.SchemaError as e:
            pytest.fail(f"The schema itself is invalid: {e.message}")

def test_feature_matrix_dimensions():
    """
    Ensure the feature matrix has the correct shape as per FR-002 (10x10 = 100 features).
    """
    features_path = Path("data/processed/persistence_images_10x10.csv")
    if not features_path.exists():
        pytest.skip("Features file not found")
    
    df = pd.read_csv(features_path)
    # Columns: molecule_id + 100 pixels
    assert df.shape[1] == 101, f"Expected 101 columns (id + 100 features), found {df.shape[1]}"
    assert "molecule_id" in df.columns
    assert all(f"pixel_{i}" in df.columns for i in range(100))

def test_feature_matrix_no_nans():
    """
    Ensure no NaN values exist in the feature matrix (Requirement for T002).
    """
    features_path = Path("data/processed/persistence_images_10x10.csv")
    if not features_path.exists():
        pytest.skip("Features file not found")
    
    df = pd.read_csv(features_path)
    assert not df.isnull().any().any(), "Feature matrix contains NaN values"