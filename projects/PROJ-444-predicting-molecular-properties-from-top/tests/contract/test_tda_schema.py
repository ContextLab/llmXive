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

def test_tda_schema_compliance():
    schema = _load_schema()
    validator = jsonschema.Draft7Validator(schema)
    df = pd.read_csv(DATA_DIR / "topological_features_10x10.csv")
    for _, row in df.iterrows():
        validator.validate(row.to_dict())