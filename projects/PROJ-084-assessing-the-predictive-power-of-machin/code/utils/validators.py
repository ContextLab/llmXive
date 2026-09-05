"""
Validation utilities for dataset and output schemas using Pydantic v2.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple
import yaml
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Dataset Schema Models (for T007b) ---

class DatasetRecord(BaseModel):
    """Represents a single row in the processed dataset."""
    smiles: str = Field(..., description="SMILES string of the reaction")
    yield_pct: float = Field(..., ge=0.0, le=100.0, description="Yield percentage")
    reaction_class: str = Field(..., description="Class of the reaction")
    fingerprint_ecfp: List[int] = Field(
        ..., length=2048, description="ECFP4 fingerprint bits"
    )
    fingerprint_maccs: List[int] = Field(
        ..., length=167, description="MACCS keys fingerprint bits"
    )

    @field_validator('fingerprint_ecfp')
    @classmethod
    def validate_ecfp(cls, v):
        if len(v) != 2048:
            raise ValueError(f"ECFP fingerprint must be length 2048, got {len(v)}")
        return v

    @field_validator('fingerprint_maccs')
    @classmethod
    def validate_maccs(cls, v):
        if len(v) != 167:
            raise ValueError(f"MACCS fingerprint must be length 167, got {len(v)}")
        return v


class DatasetSchema(BaseModel):
    """Schema definition for the dataset."""
    fields: Dict[str, Any] = Field(..., description="Field definitions")


# --- Output Schema Models (for T008b) ---

class MetricsRecord(BaseModel):
    """Performance metrics record."""
    R2: float = Field(..., description="R-squared value")
    RMSE: float = Field(..., description="Root Mean Squared Error")
    MAE: float = Field(..., description="Mean Absolute Error")


class SplitRatiosRecord(BaseModel):
    """Split ratios record."""
    train: float = Field(..., ge=0.0, le=1.0)
    val: float = Field(..., ge=0.0, le=1.0)
    test: float = Field(..., ge=0.0, le=1.0)


class OutputRecord(BaseModel):
    """Represents a model output artifact."""
    model_type: str = Field(..., description="Type of model")
    hyperparameters: Dict[str, Any] = Field(..., description="Best hyperparameters")
    metrics: MetricsRecord = Field(..., description="Test metrics")
    split_ratios: SplitRatiosRecord = Field(..., description="Split ratios used")


class OutputSchema(BaseModel):
    """Schema definition for the output."""
    model_type: Dict[str, Any] = Field(..., description="Model type definition")
    hyperparameters: Dict[str, Any] = Field(..., description="Hyperparameters definition")
    metrics: Dict[str, Any] = Field(..., description="Metrics definition")
    split_ratios: Dict[str, Any] = Field(..., description="Split ratios definition")


# --- Helper Functions ---

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema file into a dictionary."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def validate_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate DataFrame columns against a schema definition.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    expected_fields = schema.get('fields', {})
    
    for col_name, col_def in expected_fields.items():
        if col_name not in df.columns:
            errors.append(f"Missing column: {col_name}")
            continue
        
        col_type = col_def.get('type')
        if col_type == 'string':
            if not pd.api.types.is_string_dtype(df[col_name]):
                errors.append(f"Column {col_name} should be string")
        elif col_type == 'float':
            if not pd.api.types.is_float_dtype(df[col_name]):
                errors.append(f"Column {col_name} should be float")
        elif col_type == 'list of int':
            # Check first non-null value
            sample = df[col_name].dropna().iloc[0] if len(df) > 0 else None
            if sample is not None:
                if not isinstance(sample, list):
                    errors.append(f"Column {col_name} should be list")
                elif len(sample) > 0 and not isinstance(sample[0], int):
                    errors.append(f"Column {col_name} list items should be int")
                
                # Check length if specified
                if 'length' in col_def:
                    expected_len = col_def['length']
                    if len(sample) != expected_len:
                        errors.append(f"Column {col_name} list length should be {expected_len}, got {len(sample)}")
    
    return errors


def validate_fingerprint_dimensions(df: pd.DataFrame) -> List[str]:
    """Specific validation for fingerprint columns."""
    errors = []
    if 'fingerprint_ecfp' in df.columns:
        sample = df['fingerprint_ecfp'].dropna().iloc[0] if len(df) > 0 else None
        if sample and len(sample) != 2048:
            errors.append(f"ECFP length is {len(sample)}, expected 2048")
    
    if 'fingerprint_maccs' in df.columns:
        sample = df['fingerprint_maccs'].dropna().iloc[0] if len(df) > 0 else None
        if sample and len(sample) != 167:
            errors.append(f"MACCS length is {len(sample)}, expected 167")
    return errors


def validate_record_content(record: Dict[str, Any], schema_type: str) -> None:
    """
    Validate a single record dictionary against the appropriate Pydantic model.
    Raises ValidationError if invalid.
    """
    if schema_type == 'dataset':
        DatasetRecord(**record)
    elif schema_type == 'output':
        OutputRecord(**record)
    else:
        raise ValueError(f"Unknown schema type: {schema_type}")


def validate_dataset_file(data_path: Union[str, Path], schema_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate a Parquet/CSV data file against dataset.schema.yaml.
    Returns (is_valid, message).
    """
    try:
        schema = load_schema(schema_path)
        df = pd.read_parquet(data_path) if str(data_path).endswith('.parquet') else pd.read_csv(data_path)
        
        col_errors = validate_column_schema(df, schema)
        fp_errors = validate_fingerprint_dimensions(df)
        
        if col_errors or fp_errors:
            all_errors = col_errors + fp_errors
            return False, f"Validation failed: {'; '.join(all_errors)}"
        
        # Sample row validation
        if len(df) > 0:
            sample = df.iloc[0].to_dict()
            # Map pandas column names to expected field names if necessary
            # Assuming schema expects 'yield' but data might have 'yield_pct'
            if 'yield_pct' in sample and 'yield' in schema['fields']:
                sample['yield'] = sample.pop('yield_pct')
            
            validate_record_content(sample, 'dataset')
        
        return True, "Dataset valid"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_output_file(output_path: Union[str, Path], schema_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate a JSON output file against output.schema.yaml.
    Returns (is_valid, message).
    """
    try:
        # Load schema to ensure it exists and is parseable
        load_schema(schema_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Validate against Pydantic model
        OutputRecord(**data)
        
        return True, "Output valid"
    except ValidationError as e:
        return False, f"Validation failed: {e.json()}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def save_validation_report(report_path: Union[str, Path], is_valid: bool, message: str) -> None:
    """Save a validation report to a JSON file."""
    report = {
        "valid": is_valid,
        "message": message,
        "status": "PASSED" if is_valid else "FAILED"
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {report_path}: {message}")