"""
Data and Output Schema Validators using Pydantic.

This module provides validation logic for dataset records and model output records
based on the YAML schema definitions. It exposes two primary functions that are
used by the contract tests and by downstream pipeline code:

- ``validate_output_schema(payload: dict, schema_path: str)`` validates a model
  output dictionary against the ``output.schema.yaml`` contract.
- ``validate_dataset_schema(payload: dict, schema_path: str)`` validates a single
  dataset record against the ``dataset.schema.yaml`` contract.

Both functions raise ``pydantic.ValidationError`` on mismatch and ``FileNotFoundError``
if the supplied schema file does not exist.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
import pydantic
from pydantic import BaseModel, Field, ValidationError, field_validator

# Configure module‑level logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models that mirror the contract schemas
# ---------------------------------------------------------------------------

class FingerprintECFP(BaseModel):
    """Validator for ECFP fingerprint vector (2048 bits)."""
    __root__: List[bool] = Field(..., description="ECFP fingerprint vector (binary bits)")

    @field_validator("__root__")
    @classmethod
    def check_length(cls, v: List[bool]) -> List[bool]:
        if len(v) != 2048:
            raise ValueError(f"ECFP fingerprint must have exactly 2048 bits, got {len(v)}")
        return v


class FingerprintMACCS(BaseModel):
    """Validator for MACCS key fingerprint vector (167 bits)."""
    __root__: List[bool] = Field(..., description="MACCS fingerprint vector (binary bits)")

    @field_validator("__root__")
    @classmethod
    def check_length(cls, v: List[bool]) -> List[bool]:
        if len(v) != 167:
            raise ValueError(f"MACCS fingerprint must have exactly 167 bits, got {len(v)}")
        return v


class DatasetRecord(BaseModel):
    """Schema for a single row in the processed dataset."""
    smiles: str = Field(..., min_length=1, description="SMILES string of the reaction")
    # ``yield`` is the alias used in the contract; we store it internally as ``yield_value``.
    yield_value: float = Field(..., ge=0.0, le=100.0, alias="yield", description="Yield percentage")
    reaction_class: str = Field(..., min_length=1, description="Reaction class label")
    fingerprint_ecfp: FingerprintECFP
    fingerprint_maccs: FingerprintMACCS

    class Config:
        populate_by_name = True  # Allows both ``yield`` and ``yield_value`` keys


class MetricsRecord(BaseModel):
    """Schema for model evaluation metrics."""
    R2: float = Field(..., description="R-squared score")
    RMSE: float = Field(..., description="Root Mean Squared Error")
    MAE: float = Field(..., description="Mean Absolute Error")


class OutputRecord(BaseModel):
    """Schema for the model output artifact."""
    model_type: str = Field(..., description="Type of model (e.g., 'RandomForest', 'SVM')")
    hyperparameters: Dict[str, Any] = Field(..., description="Dictionary of hyperparameters used")
    metrics: MetricsRecord
    split_ratios: Dict[str, float] = Field(..., description="Train/Val/Test split ratios")

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema file and return its contents as a Python dict.

    Parameters
    ----------
    schema_path: Path
        Path to the YAML schema file.

    Returns
    -------
    dict
        Parsed YAML content.

    Raises
    ------
    FileNotFoundError
        If the schema file does not exist.
    yaml.YAMLError
        If the file cannot be parsed as valid YAML.
    """
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ---------------------------------------------------------------------------
# Public validation functions required by T001
# ---------------------------------------------------------------------------

def validate_output_schema(payload: Dict[str, Any], schema_path: str) -> None:
    """
    Validate a model output dictionary against the output contract.

    The function loads the schema file (to guarantee its existence) and then
    validates ``payload`` using the :class:`OutputRecord` Pydantic model.
    If validation fails, a ``pydantic.ValidationError`` is raised.

    Parameters
    ----------
    payload: dict
        The model output payload to validate.
    schema_path: str
        Path to the ``output.schema.yaml`` file.

    Raises
    ------
    FileNotFoundError
        If ``schema_path`` does not point to an existing file.
    pydantic.ValidationError
        If ``payload`` does not satisfy the contract.
    """
    schema_file = Path(schema_path)
    # Ensure the schema file exists – we don't actually need its contents
    # for Pydantic validation, but the contract explicitly requires the file.
    _load_schema(schema_file)

    logger.debug("Validating output payload against OutputRecord model.")
    # Pydantic will raise ValidationError on mismatch.
    OutputRecord(**payload)
    logger.info("Output payload validation successful.")

def validate_dataset_schema(payload: Dict[str, Any], schema_path: str) -> None:
    """
    Validate a single dataset record against the dataset contract.

    Parameters
    ----------
    payload: dict
        A dictionary representing one row of the processed dataset.
    schema_path: str
        Path to the ``dataset.schema.yaml`` file.

    Raises
    ------
    FileNotFoundError
        If ``schema_path`` does not point to an existing file.
    pydantic.ValidationError
        If ``payload`` does not satisfy the contract.
    """
    schema_file = Path(schema_path)
    _load_schema(schema_file)

    logger.debug("Validating dataset record against DatasetRecord model.")
    DatasetRecord(**payload)
    logger.info("Dataset record validation successful.")

# ---------------------------------------------------------------------------
# Existing convenience entry points (kept for backward compatibility)
# ---------------------------------------------------------------------------

def validate_dataset_schema() -> bool:  # pragma: no cover
    """
    Backward‑compatible wrapper that validates the dataset schema file itself.
    Returns ``True`` if the schema file exists and a mock row passes validation.
    """
    try:
        if not Path("specs/001-assessing-the-predictive-power-of-machin/contracts/dataset.schema.yaml").exists():
            raise FileNotFoundError("Dataset schema file missing")
        mock_row = {
            "smiles": "CC(=O)O",
            "yield": 50.0,
            "reaction_class": "esterification",
            "fingerprint_ecfp": [True] * 2048,
            "fingerprint_maccs": [True] * 167,
        }
        validate_dataset_schema(mock_row, "specs/001-assessing-the-predictive-power-of-machin/contracts/dataset.schema.yaml")
        return True
    except Exception as e:
        logger.error(f"Dataset schema validation failed: {e}")
        return False

def validate_output_schema() -> bool:  # pragma: no cover
    """
    Backward‑compatible wrapper that validates the output schema file itself.
    Returns ``True`` if the schema file exists and a mock output passes validation.
    """
    try:
        if not Path("specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml").exists():
            raise FileNotFoundError("Output schema file missing")
        mock_output = {
            "model_type": "RandomForest",
            "hyperparameters": {"n_estimators": 100, "max_depth": 10},
            "metrics": {"R2": 0.85, "RMSE": 12.5, "MAE": 8.2},
            "split_ratios": {"train": 0.7, "val": 0.15, "test": 0.15},
        }
        validate_output_schema(mock_output, "specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml")
        return True
    except Exception as e:
        logger.error(f"Output schema validation failed: {e}")
        return False

if __name__ == "__main__":  # pragma: no cover
    # Simple CLI for manual sanity checks
    if len(sys.argv) != 3:
        print("Usage: python validators.py <payload_json> <schema_path>")
        sys.exit(1)
    payload_path = Path(sys.argv[1])
    schema_path = sys.argv[2]
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    # Heuristically decide which validator to call based on schema filename
    if "output" in schema_path:
        validate_output_schema(payload, schema_path)
    else:
        validate_dataset_schema(payload, schema_path)
    print("Validation succeeded.")
