"""
Schema validation utilities using Pydantic v2.

Provides:
- DatasetRecord, DatasetSchema: Pydantic models for dataset validation
- OutputRecord, OutputSchema: Pydantic models for output validation
- load_schema: Load YAML schema files
- validate_dataset_file: Validate a Parquet/CSV file against schema
- validate_output_file: Validate output JSON against schema
"""
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Dataset Schema Models ---

class DatasetRecord(BaseModel):
    """Schema for a single dataset record."""
    smiles: str = Field(..., description="SMILES string of the reaction")
    yield_value: float = Field(..., ge=0.0, le=100.0, description="Yield percentage")
    reaction_class: str = Field(..., description="Reaction class label")
    fingerprint_ecfp: List[int] = Field(..., min_length=2048, max_length=2048, description="ECFP4 fingerprint")
    fingerprint_maccs: List[int] = Field(..., min_length=167, max_length=167, description="MACCS fingerprint")

    @field_validator('fingerprint_ecfp')
    @classmethod
    def validate_ecfp(cls, v):
        if len(v) != 2048:
            raise ValueError(f"ECFP fingerprint must have length 2048, got {len(v)}")
        if not all(x in [0, 1] for x in v):
            raise ValueError("ECFP fingerprint must contain only 0s and 1s")
        return v

    @field_validator('fingerprint_maccs')
    @classmethod
    def validate_maccs(cls, v):
        if len(v) != 167:
            raise ValueError(f"MACCS fingerprint must have length 167, got {len(v)}")
        if not all(x in [0, 1] for x in v):
            raise ValueError("MACCS fingerprint must contain only 0s and 1s")
        return v

class DatasetSchema(BaseModel):
    """Schema definition for the dataset."""
    fields: Dict[str, Dict[str, Any]]
    validation_rules: Optional[Dict[str, Any]] = None

# --- Output Schema Models ---

class MetricsRecord(BaseModel):
    """Schema for model metrics."""
    R2: float = Field(..., description="R-squared value")
    RMSE: float = Field(..., description="Root Mean Squared Error")
    MAE: float = Field(..., description="Mean Absolute Error")

class OutputRecord(BaseModel):
    """Schema for a model output record."""
    model_type: str = Field(..., description="Type of model (e.g., 'RandomForest', 'SVM')")
    hyperparameters: Dict[str, Any] = Field(..., description="Model hyperparameters")
    metrics: MetricsRecord = Field(..., description="Performance metrics")
    split_ratios: Dict[str, float] = Field(..., description="Train/Val/Test split ratios")

class OutputSchema(BaseModel):
    """Schema definition for model outputs."""
    records: List[OutputRecord]

# --- Schema Loading and Validation Functions ---

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema

def validate_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate DataFrame columns against schema definition."""
    errors = []
    expected_columns = schema.get('fields', {}).keys()
    
    if set(df.columns) != set(expected_columns):
        missing = set(expected_columns) - set(df.columns)
        extra = set(df.columns) - set(expected_columns)
        if missing:
            errors.append(f"Missing columns: {missing}")
        if extra:
            errors.append(f"Extra columns: {extra}")
    
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame) -> List[str]:
    """Validate fingerprint column dimensions."""
    errors = []
    
    if 'fingerprint_ecfp' in df.columns:
        for idx, fp in enumerate(df['fingerprint_ecfp']):
            if len(fp) != 2048:
                errors.append(f"Row {idx}: ECFP length is {len(fp)}, expected 2048")
                break  # Only report first error
    
    if 'fingerprint_maccs' in df.columns:
        for idx, fp in enumerate(df['fingerprint_maccs']):
            if len(fp) != 167:
                errors.append(f"Row {idx}: MACCS length is {len(fp)}, expected 167")
                break
    
    return errors

def validate_record_content(df: pd.DataFrame) -> List[str]:
    """Validate content of records (e.g., yield range, fingerprint values)."""
    errors = []
    
    # Check yield range
    if 'yield' in df.columns or 'yield_value' in df.columns:
        yield_col = 'yield' if 'yield' in df.columns else 'yield_value'
        if df[yield_col].min() < 0.0 or df[yield_col].max() > 100.0:
            errors.append(f"Yield values out of range [0, 100]: min={df[yield_col].min()}, max={df[yield_col].max()}")
    
    # Check fingerprint values (0 or 1)
    if 'fingerprint_ecfp' in df.columns:
        for idx, fp in enumerate(df['fingerprint_ecfp']):
            if not all(x in [0, 1] for x in fp):
                errors.append(f"Row {idx}: ECFP contains values other than 0 or 1")
                break
    
    if 'fingerprint_maccs' in df.columns:
        for idx, fp in enumerate(df['fingerprint_maccs']):
            if not all(x in [0, 1] for x in fp):
                errors.append(f"Row {idx}: MACCS contains values other than 0 or 1")
                break
    
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: str) -> Dict[str, Any]:
    """
    Validate a DataFrame against a dataset schema.
    
    Returns:
        Dict with 'valid' (bool) and 'errors' (list)
    """
    errors = []
    
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        return {"valid": False, "errors": [str(e)]}
    
    # Check columns
    col_errors = validate_column_schema(df, schema)
    errors.extend(col_errors)
    
    # Check fingerprint dimensions
    fp_errors = validate_fingerprint_dimensions(df)
    errors.extend(fp_errors)
    
    # Check content
    content_errors = validate_record_content(df)
    errors.extend(content_errors)
    
    # Check for null values in required fields
    required_fields = schema.get('fields', {}).keys()
    for field in required_fields:
        if field in df.columns:
            if df[field].isna().any():
                errors.append(f"Column '{field}' contains null values")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "row_count": len(df),
        "timestamp": datetime.now().isoformat()
    }

def validate_dataset_file(file_path: str, schema_path: str) -> Dict[str, Any]:
    """Validate a Parquet/CSV file against a schema."""
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "errors": [f"File not found: {file_path}"]}
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(file_path)
    elif path.suffix == '.csv':
        df = pd.read_csv(file_path)
    else:
        return {"valid": False, "errors": ["Unsupported file format"]}
    
    return validate_dataset(df, schema_path)

def validate_output_file(file_path: str, schema_path: str) -> Dict[str, Any]:
    """Validate an output JSON file against a schema."""
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "errors": [f"File not found: {file_path}"]}
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Basic validation (full Pydantic validation would require restructuring)
    errors = []
    if not isinstance(data, dict):
        errors.append("Output must be a dictionary")
    else:
        required_keys = ['model_type', 'hyperparameters', 'metrics', 'split_ratios']
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }

def save_validation_report(report: Dict[str, Any], output_path: str):
    """Save a validation report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")
