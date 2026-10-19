import jsonschema
import yaml
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-predicting-molecular-properties-from-top" / "contracts"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

def _load_schema():
    schema_path = CONTRACTS_DIR / "feature_matrix.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def test_file_exists():
    csv_path = DATA_DIR / "topological_features_10x10.csv"
    assert csv_path.exists(), "Topological features CSV missing"

def test_schema_compliance():
    schema = _load_schema()
    validator = jsonschema.Draft7Validator(schema)
    df = pd.read_csv(DATA_DIR / "topological_features_10x10.csv")
    for _, row in df.iterrows():
        record = row.to_dict()
        validator.validate(record)

def test_no_nan_values():
    df = pd.read_csv(DATA_DIR / "topological_features_10x10.csv")
    assert not df.isnull().any().any(), "NaN values found in TDA feature CSV"

def test_image_vector_length():
    df = pd.read_csv(DATA_DIR / "topological_features_10x10.csv")
    pixel_cols = [c for c in df.columns if c.startswith("pixel_")]
    assert len(pixel_cols) == 100, "Expected 100 pixel columns for 10x10 image"

def test_molecule_id_is_string():
    df = pd.read_csv(DATA_DIR / "topological_features_10x10.csv")
    assert df["molecule_id"].apply(lambda x: isinstance(x, str)).all(), "molecule_id must be string"

def test_valid_molecules_count():
    df = pd.read_csv(DATA_DIR / "topological_features_10x10.csv")
    # The count should match the number of rows in filtered_esol.csv
    filtered_path = PROJECT_ROOT / "data" / "processed" / "filtered_esol.csv"
    filtered_df = pd.read_csv(filtered_path)
    assert df.shape[0] == filtered_df.shape[0], "Row count mismatch"