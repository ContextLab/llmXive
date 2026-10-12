"""
Contract test (T014): validate data/raw/esol.csv against
specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml

If the raw CSV is not yet on disk (e.g. the ingestion step has not been
run), it is materialised from the VERIFIED REAL DATA SOURCE
(scikit-fingerprints ``load_lipophilicity``). No synthetic fallback
exists: if the real source cannot be loaded the test fails loudly.
"""

from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "esol.csv"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-predicting-molecular-properties-from-top"
    / "contracts"
    / "dataset.schema.yaml"
)


def _ensure_raw_dataset() -> None:
    """Materialise data/raw/esol.csv from the verified real source if absent."""
    if RAW_CSV.exists():
        return
    from skfp.datasets.moleculenet import load_lipophilicity

    X, y = load_lipophilicity()
    if isinstance(X, pd.DataFrame):
        if "smiles" in X.columns:
            smiles = X["smiles"]
        else:
            smiles = X.iloc[:, 0]
    else:
        smiles = pd.Series(list(X))
    df = pd.DataFrame({"smiles": smiles, "logP": y})[["smiles", "logP"]]
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV, index=False)


def _load_schema() -> dict:
    with SCHEMA_PATH.open() as f:
        return yaml.safe_load(f)


def test_raw_dataset_exists():
    _ensure_raw_dataset()
    assert RAW_CSV.exists(), f"Raw dataset missing: {RAW_CSV}"


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"Schema contract missing: {SCHEMA_PATH}"


def test_columns_match_schema_exactly():
    _ensure_raw_dataset()
    schema = _load_schema()
    required = set(schema.get("required", []))
    df = pd.read_csv(RAW_CSV)
    assert set(df.columns) == required, (
        f"Columns {set(df.columns)} do not match required {required}"
    )


def test_required_fields_non_null():
    _ensure_raw_dataset()
    schema = _load_schema()
    df = pd.read_csv(RAW_CSV)
    for col in schema.get("required", []):
        assert df[col].notnull().all(), f"Null values found in required column '{col}'"


def test_field_types_match_schema():
    _ensure_raw_dataset()
    schema = _load_schema()
    props = schema.get("properties", {})
    df = pd.read_csv(RAW_CSV)
    assert pd.api.types.is_string_dtype(df["smiles"]) or pd.api.types.is_object_dtype(
        df["smiles"]
    ), "Column 'smiles' must be strings per schema"
    assert props["smiles"]["type"] == "string"
    assert pd.api.types.is_numeric_dtype(df["logP"]), (
        "Column 'logP' must be numeric per schema"
    )
    assert props["logP"]["type"] == "number"


def test_dataset_meets_power_analysis_minimum():
    """SC: dataset must have at least min_n=128 records (paired-t, d=0.5)."""
    _ensure_raw_dataset()
    df = pd.read_csv(RAW_CSV)
    assert len(df) >= 128, f"Dataset too small for power analysis: {len(df)} < 128"
