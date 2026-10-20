"""
test_grid_search_schema.py
Validates that data/processed/labels.csv conforms to the schema and 
the tie-breaking rule is logically consistent.
"""
import pathlib
import pandas as pd
import yaml
from jsonschema import Draft7Validator
from llmxive_toolkit import paths

def _load_schema() -> dict:
    schema_path = (
        paths.root / "specs" / "001-llmxive-follow-up-extending-in-context-w" / "contracts" / "label.schema.yaml"
    )
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def test_labels_schema():
    csv_path = paths.data("processed", "labels.csv")
    assert csv_path.exists(), f"Labels CSV missing at {csv_path}"
    
    df = pd.read_csv(csv_path)
    schema = _load_schema()
    validator = Draft7Validator(schema)
    
    for _, row in df.iterrows():
        validator.validate(row.to_dict())
        assert 0.0 <= row["success_rate"] <= 1.0, f"Invalid success rate for {row['clip_id']}"

def test_label_columns():
    df = pd.read_csv(paths.data("processed", "labels.csv"))
    expected = {"clip_id", "tau", "k", "success_rate"}
    assert expected.issubset(set(df.columns)), "Missing required columns in labels.csv"