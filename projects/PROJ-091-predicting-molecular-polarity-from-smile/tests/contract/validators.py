"""
Pydantic models for validating dataset and model output artifacts.

These models are used in the contract tests to ensure that the
descriptor matrix and the model evaluation JSON conform to the
expected schema.
"""

from pydantic import BaseModel, validator, root_validator
from typing import Any, Dict

class DescriptorMatrix(BaseModel):
    """Model representing a single row of the descriptor matrix."""

    smiles: str
    target: float

    class Config:
        # Allow additional descriptor columns (e.g., desc_* fields)
        extra = "allow"

    @root_validator
    def check_descriptor_columns(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure that any extra fields (beyond ``smiles`` and ``target``)
        start with the ``desc_`` prefix. This mirrors the contract that
        all descriptor columns are named ``desc_<descriptor_name>``.
        """
        for key in values:
            if key in {"smiles", "target"}:
                continue
            if not key.startswith("desc_"):
                raise ValueError(f"Descriptor column '{key}' does not start with 'desc_'")
        return values

class ModelOutput(BaseModel):
    """Model representing the JSON output of model evaluation."""

    r2: float
    rmse: float
    null_r2: float
    improvement: float

    class Config:
        # Allow any extra fields that the contract schema may contain
        extra = "allow"

    @validator("r2", "rmse", "null_r2", "improvement")
    def non_negative(cls, v, field):
        """All metrics should be numeric; allow negative r2 for null model comparison."""
        if not isinstance(v, (int, float)):
            raise TypeError(f"{field.name} must be a number")
        return float(v)
