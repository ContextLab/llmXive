"""
Pydantic validators for contract tests.

The original implementation used the deprecated ``@root_validator`` from
Pydantic v1, which caused import errors under Pydantic v2.  This module
provides lightweight, version‑compatible models that validate the
essential structure of the descriptor matrix rows and the model‑output
JSON files used throughout the pipeline.

The models are deliberately permissive (``extra = "allow"``) so they do
not need to be kept in lock‑step with every new descriptor column that
may be added in the future.  They still enforce the core schema
requirements defined in the contract specifications:
  * ``smiles`` must be a string.
  * ``target`` must be a number (float or int).
  * All columns whose name starts with ``desc_`` must be numeric.
  * Boolean flag columns must be of type ``bool``.
For model output we only require that the top‑level keys are present and
of the correct basic type.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError, model_validator

class DescriptorMatrix(BaseModel):
    """Validate a single row of the descriptor matrix."""

    smiles: str
    target: float
    stereochemistry_flag: bool
    flexible_flag: bool

    # Allow any additional descriptor columns (they will be validated
    # dynamically in ``model_validator``).
    class Config:
        extra = "allow"

    @model_validator(mode="before")
    @classmethod
    def check_descriptor_columns(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure that any column whose name starts with ``desc_`` is numeric.
        """
        for key, val in values.items():
            if key.startswith("desc_"):
                if not isinstance(val, (int, float)):
                    raise ValueError(f"Descriptor column '{key}' must be numeric, got {type(val)}")
        return values

class ModelOutput(BaseModel):
    """Validate the JSON output produced by the model evaluation step."""

    r2_score: float = Field(..., description="Coefficient of determination")
    rmse: float = Field(..., description="Root‑mean‑square error")
    baseline_r2: float = Field(..., description="R² of the null (mean) model")
    # Additional keys are allowed; they may contain SHAP summaries, etc.
    class Config:
        extra = "allow"

    @model_validator(mode="before")
    @classmethod
    def ensure_numeric_metrics(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that the required metric fields are numeric.
        """
        required = ["r2_score", "rmse", "baseline_r2"]
        for key in required:
            if key not in values:
                raise ValueError(f"Missing required metric '{key}'")
            if not isinstance(values[key], (int, float)):
                raise ValueError(f"Metric '{key}' must be numeric, got {type(values[key])}")
        return values
