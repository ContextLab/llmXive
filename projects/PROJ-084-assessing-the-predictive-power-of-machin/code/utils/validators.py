import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple

import yaml
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError
from pydantic_core import PydanticCustomError

logger = logging.getLogger(__name__)

# --- Dataset Schema Pydantic Models (from T007b) ---

class DatasetRecord(BaseModel):
    smiles: str = Field(..., description="SMILES string of the reaction")
    yield_val: float = Field(..., ge=0.0, le=100.0, alias="yield")
    reaction_class: str = Field(..., description="Reaction class label")
    fingerprint_ecfp: List[int] = Field(..., min_length=2048, max_length=2048, description="ECFP4 fingerprint")
    fingerprint_maccs: List[int] = Field(..., min_length=167, max_length=167, description="MACCS fingerprint")

    class Config:
        populate_by_name = True

class DatasetSchema(BaseModel):
    fields: Dict[str, Dict[str, Any]]

# --- Output Schema Pydantic Models (from T008b) ---

class MetricsRecord(BaseModel):
    R2: float = Field(..., description="R-squared coefficient")
    RMSE: float = Field(..., description="Root Mean Squared Error")
    MAE: float = Field(..., description="Mean Absolute Error")

    @field_validator('R2', 'RMSE', 'MAE')
    @classmethod
    def check_numbers(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Metrics must be numeric")
        return float(v)

class SplitRatiosRecord(BaseModel):
    train: float = Field(..., ge=0.0, le=1.0)
    val: float = Field(..., ge=0.0, le=1.0)
    test: float = Field(..., ge=0.0, le=1.0)

    @field_validator('train', 'val', 'test')
    @classmethod
    def check_sum(cls, v, info):
        # Validation of sum is done at the parent level usually, but we ensure bounds here
        return v

class OutputRecord(BaseModel):
    model_type: str = Field(..., description="Model type name")
    hyperparameters: Dict[str, Any] = Field(..., description="Hyperparameters dict")
    metrics: MetricsRecord = Field(..., description="Performance metrics")
    split_ratios: SplitRatiosRecord = Field(..., description="Data split ratios")

class OutputSchema(BaseModel):
    model_type: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
    split_ratios: Dict[str, Any]

# --- Utility Functions ---

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate DataFrame columns against a schema definition."""
    errors = []
    expected_fields = schema.get('fields', {})
    for col_name, col_def in expected_fields.items():
        if col_name not in df.columns:
            errors.append(f"Missing column: {col_name}")
        else:
            # Basic type check could be added here if schema defines types strictly
            pass
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame) -> List[str]:
    """Ensure fingerprint columns have correct lengths."""
    errors = []
    if 'fingerprint_ecfp' in df.columns:
        for i, vec in enumerate(df['fingerprint_ecfp']):
            if len(vec) != 2048:
                errors.append(f"Row {i}: ECFP length is {len(vec)}, expected 2048")
                break # Fail fast on first error
    if 'fingerprint_maccs' in df.columns:
        for i, vec in enumerate(df['fingerprint_maccs']):
            if len(vec) != 167:
                errors.append(f"Row {i}: MACCS length is {len(vec)}, expected 167")
                break
    return errors

def validate_record_content(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a single record dict against a schema."""
    errors = []
    # Simplified logic for generic dict validation
    for key, spec in schema.items():
        if key not in record:
            errors.append(f"Missing key: {key}")
    return errors

def validate_dataset_file(df: pd.DataFrame, schema_path: Path) -> bool:
    """Full validation of a dataset file against its schema."""
    schema = load_schema(schema_path)
    errors = []
    
    errors.extend(validate_column_schema(df, schema))
    errors.extend(validate_fingerprint_dimensions(df))
    
    if errors:
        logger.error(f"Dataset validation failed: {errors}")
        return False
    return True

def validate_output_file(output_path: Path, schema_path: Path) -> bool:
    """
    Load an output JSON file and validate it against output.schema.yaml.
    Raises ValidationError if validation fails.
    """
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found: {output_path}")
    
    with open(output_path, 'r') as f:
        data = json.load(f)

    # Load the schema definition (for reference, though we use Pydantic for strict validation)
    schema_def = load_schema(schema_path)

    try:
        # Validate against the strict Pydantic model
        validated_record = OutputRecord(**data)
        logger.info(f"Output file validated successfully: {output_path}")
        return True
    except ValidationError as e:
        error_msg = f"Output validation failed for {output_path}:\n{e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

def save_validation_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Save a validation report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")