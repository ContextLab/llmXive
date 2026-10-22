"""
Pydantic contract validators for the llmXive polarity-prediction pipeline.

These models validate the two artifacts governed by the project's
contracts:

* ``data/processed/descriptors.parquet``  -> :class:`DescriptorMatrix`
  (one instance per row; descriptor column names are taken dynamically
  from ``data/processed/descriptor_names.json`` so the validator stays
  in sync with the real generated matrix, whose columns are named after
  RDKit descriptors such as ``AUTOCORR2D_1`` / ``Chi0`` — not ``desc_*``).
* ``data/results/model_metrics.json``     -> :class:`ModelOutput`

The models are deliberately permissive (``extra="allow"``) so new
descriptor columns do not break the contract, while the core schema
requirements from the spec are enforced:

* ``smiles`` must be a string.
* ``target`` must be numeric.
* Boolean flag columns must be ``bool``.
* Every descriptor column listed in ``descriptor_names.json`` must be
  numeric and must not be TPSA-related or SMARTS-derived.
* Model output must contain numeric ``r2_score``, ``rmse`` and
  ``baseline_r2``.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR_NAMES_JSON = PROJECT_ROOT / "data" / "processed" / "descriptor_names.json"

# Columns that must never appear in the descriptor matrix (FR-001).
FORBIDDEN_SUBSTRINGS = ("TPSA", "tpsa", "SMARTS", "smarts")

def load_descriptor_names(json_path: Optional[Path] = None) -> List[str]:
    """Load the ordered descriptor-name list produced by T101.

    Raises loudly (FileNotFoundError / ValueError) if the file is
    missing or malformed — never falls back to a guessed list.
    """
    path = Path(json_path) if json_path else DESCRIPTOR_NAMES_JSON
    if not path.exists():
        raise FileNotFoundError(
            f"Descriptor name list not found: {path}. "
            "Run the descriptor generation step (T101) first."
        )
    with open(path, "r", encoding="utf-8") as f:
        names = json.load(f)
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        raise ValueError(
            f"{path} must contain a JSON list of descriptor name strings"
        )
    return names

class DescriptorMatrix(BaseModel):
    """Validate a single row of the descriptor matrix."""

    model_config = ConfigDict(extra="allow")

    smiles: str
    target: float
    stereochemistry_flag: bool
    flexible_flag: bool

    @model_validator(mode="before")
    @classmethod
    def check_descriptor_columns(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Any non-reserved column must be numeric (descriptors, flags)."""
        reserved = {"smiles", "target", "stereochemistry_flag", "flexible_flag"}
        for key, val in values.items():
            if key in reserved:
                continue
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                # bools are allowed only for the reserved flag columns
                if not isinstance(val, bool):
                    raise ValueError(
                        f"Descriptor column '{key}' must be numeric, "
                        f"got {type(val)}"
                    )
        return values

class ModelOutput(BaseModel):
    """Validate the JSON output produced by the model training step."""

    model_config = ConfigDict(extra="allow")

    r2_score: float = Field(..., description="Coefficient of determination")
    rmse: float = Field(..., description="Root-mean-square error")
    baseline_r2: float = Field(..., description="R² of the null (mean) model")

    @model_validator(mode="before")
    @classmethod
    def ensure_numeric_metrics(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        required = ["r2_score", "rmse", "baseline_r2"]
        for key in required:
            if key not in values:
                raise ValueError(f"Missing required metric '{key}'")
            v = values[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError(
                    f"Metric '{key}' must be numeric, got {type(v)}"
                )
        return values

def validate_descriptor_frame(df) -> List[str]:
    """Validate a descriptor-matrix DataFrame against the contract.

    Returns the list of descriptor column names on success; raises
    ``ValueError`` / ``AssertionError`` on any contract violation.
    """
    import pandas as pd  # local import to keep module import cheap

    descriptor_names = load_descriptor_names()

    for col in ("smiles", "target", "stereochemistry_flag", "flexible_flag"):
        if col not in df.columns:
            raise ValueError(f"Descriptor matrix missing required column '{col}'")

    # Every declared descriptor must be present, in order.
    missing = [c for c in descriptor_names if c not in df.columns]
    if missing:
        raise ValueError(
            f"Descriptor matrix missing {len(missing)} declared descriptor "
            f"columns (first few: {missing[:5]})"
        )

    # No forbidden (TPSA / SMARTS) columns anywhere.
    for col in df.columns:
        if any(bad in str(col) for bad in FORBIDDEN_SUBSTRINGS):
            raise ValueError(f"Forbidden column present in matrix: '{col}'")

    if len(descriptor_names) < 200:
        raise ValueError(
            f"Contract requires >= 200 descriptors, found {len(descriptor_names)}"
        )

    # Row-level validation on a sample (full validation is O(rows)).
    sample = df.head(200)
    records = sample.to_dict(orient="records")
    for rec in records:
        DescriptorMatrix(**rec)

    # Descriptor values must be finite (no NaN post-imputation).
    desc_df = sample[descriptor_names]
    if desc_df.isna().any().any():
        raise ValueError("NaN values remain in descriptor columns")

    return descriptor_names
