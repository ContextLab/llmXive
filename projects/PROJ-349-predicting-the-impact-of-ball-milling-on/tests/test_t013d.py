import pandas as pd
from src.utils.validate_schema import load_schema, validate_schema

def test_verified_static_subset_exists():
    try:
        df = pd.read_csv("data/fallback/verified_static_subset.csv")
        assert df is not None
        assert len(df) >= 150
    except FileNotFoundError:
        assert False, "File not found"

def test_verified_static_subset_schema():
    try:
        schema = load_schema("contracts/dataset.schema.yaml")
        df = pd.read_csv("data/fallback/verified_static_subset.csv")
        validate_schema(df, schema)
    except Exception as e:
        assert False, f"Schema validation failed: {e}"
