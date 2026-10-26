"""
Pydantic validators for contract tests.
Provides models for descriptor matrix and model output,
and helper functions used by the contract test suite.
"""

from pathlib import Path
import json
from typing import List, Any

import pandas as pd
from pydantic import BaseModel, Field, field_validator

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DESCRIPTORS_PARQUET = PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
DESCRIPTOR_NAMES_JSON = PROJECT_ROOT / "data" / "processed" / "descriptor_names.json"


def load_descriptor_names() -> List[str]:
    """Load the list of descriptor names from the JSON file."""
    with open(DESCRIPTOR_NAMES_JSON, "r", encoding="utf-8") as f:
        names = json.load(f)
    return names


def validate_descriptor_frame(df: pd.DataFrame) -> List[str]:
    """
    Validate that the DataFrame contains the expected descriptor columns.
    Returns the list of descriptor column names (excluding metadata columns).
    """
    required_meta = {"smiles", "target", "stereochemistry_flag", "flexible_flag"}
    df_cols = set(df.columns)
    missing_meta = required_meta - df_cols
    if missing_meta:
        raise ValueError(f"Missing required metadata columns: {missing_meta}")

    descriptor_cols = [c for c in df.columns if c not in required_meta]
    # Ensure descriptor columns match the JSON list (order not important)
    expected = set(load_descriptor_names())
    actual = set(descriptor_cols)
    if not expected.issubset(actual):
        missing = expected - actual
        raise ValueError(f"Descriptor columns missing from DataFrame: {missing}")

    return descriptor_cols


# -------------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------------
class DescriptorMatrix(BaseModel):
    """
    Model representing a single row of the descriptor matrix.
    All descriptor fields are optional floats because they may be
    imputed; the presence of the column is enforced by the schema
    validator in the test suite.
    """

    smiles: str
    target: float
    stereochemistry_flag: bool
    flexible_flag: bool

    # Dynamically allow any descriptor column (float or int)
    @field_validator("*", mode="before")
    def allow_numeric(cls, v: Any) -> Any:
        if isinstance(v, (int, float)):
            return float(v)
        return v

    class Config:
        extra = "allow"


class ModelOutput(BaseModel):
    """
    Model output metrics schema.
    """

    r2_score: float = Field(..., ge=0.0)
    rmse: float = Field(..., ge=0.0)
    baseline_r2: float = Field(..., ge=0.0)

    @field_validator("r2_score")
    def r2_must_be_non_negative(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("R² must be non‑negative")
        return v

    @field_validator("rmse")
    def rmse_non_negative(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("RMSE must be non‑negative")
        return v

    @field_validator("baseline_r2")
    def baseline_non_negative(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("Baseline R² must be non‑negative")
        return v
