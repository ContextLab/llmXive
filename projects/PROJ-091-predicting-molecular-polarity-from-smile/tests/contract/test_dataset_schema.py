"""
Contract test: the real descriptor matrix conforms to the dataset schema.

Validates ``data/processed/descriptors.parquet`` (produced by T101)
against ``data/processed/descriptor_names.json`` using the Pydantic
validators in ``tests/contract/validators.py``.

If the real artifact has not been generated yet (T101 pending), the
test is SKIPPED with an explicit message — it never fabricates data.
"""

import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from validators import (  # noqa: E402
    DescriptorMatrix,
    ModelOutput,  # noqa: F401  (re-exported for sibling tests)
    load_descriptor_names,
    validate_descriptor_frame,
)

PROJECT_ROOT = THIS_DIR.parents[1]
DESCRIPTORS_PARQUET = PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
DESCRIPTOR_NAMES_JSON = PROJECT_ROOT / "data" / "processed" / "descriptor_names.json"


def test_descriptor_names_json_exists_and_is_list():
    if not DESCRIPTOR_NAMES_JSON.exists():
        pytest.skip(
            "data/processed/descriptor_names.json not yet generated (T101 pending)"
        )
    names = load_descriptor_names()
    assert isinstance(names, list)
    assert len(names) >= 200, f"expected >= 200 descriptors, got {len(names)}"
    assert all(isinstance(n, str) and n for n in names)


def test_descriptor_names_exclude_tpsa_and_smarts():
    if not DESCRIPTOR_NAMES_JSON.exists():
        pytest.skip(
            "data/processed/descriptor_names.json not yet generated (T101 pending)"
        )
    names = load_descriptor_names()
    for n in names:
        assert "TPSA" not in n and "tpsa" not in n.upper(), f"TPSA leak: {n}"
        assert "SMARTS" not in n.upper(), f"SMARTS leak: {n}"


def test_real_descriptor_matrix_conforms():
    if not DESCRIPTORS_PARQUET.exists():
        pytest.skip(
            "data/processed/descriptors.parquet not yet generated (T101 pending)"
        )
    import pandas as pd

    df = pd.read_parquet(DESCRIPTORS_PARQUET)
    descriptor_names = validate_descriptor_frame(df)

    # Required metadata columns present with correct dtypes.
    assert df["smiles"].dtype == object, "smiles column must be strings"
    assert df["target"].dtype.kind == "f", "target column must be float"
    assert df["stereochemistry_flag"].dtype == bool
    assert df["flexible_flag"].dtype == bool

    # Flag proportion constraints (SC-006 / FR-009).
    stereo_frac = float(df["stereochemistry_flag"].mean())
    assert stereo_frac <= 0.05, (
        f"stereochemistry_flag proportion {stereo_frac:.4f} exceeds 5%"
    )

    # At least one row validated through the Pydantic model directly.
    first = df.iloc[0].to_dict()
    DescriptorMatrix(**first)

    assert len(descriptor_names) >= 200
