"""
Contract test for the ESOL dataset schema.
Ensures that the raw CSV written by the ingestion script contains exactly the
required columns ``smiles`` and ``logP``.
"""

import json
from pathlib import Path

import pandas as pd
import yaml

def test_schema_matches():
    schema_path = Path(
        "specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml"
    )
    raw_path = Path("data/raw/esol.csv")
    assert raw_path.exists(), f"Raw dataset not found at {raw_path}"

    df = pd.read_csv(raw_path)

    with schema_path.open() as f:
        schema = yaml.safe_load(f)

    required = set(schema.get("required", []))
    present = set(df.columns)

    assert present == required, f"Columns mismatch. Expected {required}, got {present}"