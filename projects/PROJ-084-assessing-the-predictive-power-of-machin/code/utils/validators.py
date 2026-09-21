import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple
import yaml
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List as TypedList

logger = logging.getLogger(__name__)

# Pydantic Models for Dataset Validation
class DatasetRecord(BaseModel):
    smiles: str = Field(..., min_length=1)
    yield_val: float = Field(..., ge=0.0, le=100.0, alias="yield")
    reaction_class: str = Field(..., min_length=1)
    fingerprint_ecfp: TypedList[int] = Field(..., min_length=2048, max_length=2048)
    fingerprint_maccs: TypedList[int] = Field(..., min_length=167, max_length=167)

    # Adjust field name for pydantic alias mapping if needed, 
    # but we validate the raw dict structure via a wrapper or direct check.
    # For strict schema enforcement on dicts, we rely on the schema loading logic below.

class DatasetSchema(BaseModel):
    type: str
    properties: Dict[str, Any]
    required: TypedList[str]

class MetricsRecord(BaseModel):
    R2: float
    RMSE: float
    MAE: float

class SplitRatiosRecord(BaseModel):
    train: float
    val: float
    test: float

class OutputRecord(BaseModel):
    model_type: str
    hyperparameters: Dict[str, Any]
    metrics: MetricsRecord
    split_ratios: SplitRatiosRecord

class OutputSchema(BaseModel):
    type: str
    properties: Dict[str, Any]
    required: TypedList[str]

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema file into a dictionary."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
        schema = yaml.safe_load(f)
    
    if schema is None:
        raise ValueError(f"Schema file {path} is empty or invalid YAML")
    
    return schema

def validate_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate DataFrame columns against schema properties."""
    errors = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Check required columns
    missing_cols = set(required) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check types and constraints (basic check)
    for col, col_schema in properties.items():
        if col in df.columns:
            dtype = df[col].dtype
            col_type = col_schema.get("type")
            
            if col_type == "string" and not pd.api.types.is_string_dtype(dtype):
                errors.append(f"Column '{col}' should be string type, got {dtype}")
            elif col_type == "number" and not pd.api.types.is_numeric_dtype(dtype):
                errors.append(f"Column '{col}' should be numeric type, got {dtype}")
            elif col_type == "array" and not isinstance(df[col].iloc[0], (list, np.ndarray)):
                # Check first non-null if possible
                first_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
                if first_val is not None and not isinstance(first_val, (list, np.ndarray)):
                    errors.append(f"Column '{col}' should be array type, got {type(first_val)}")
    
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate array lengths for fingerprint columns."""
    errors = []
    properties = schema.get("properties", {})
    
    for col_name, col_schema in properties.items():
        if col_schema.get("type") == "array":
            min_items = col_schema.get("minItems")
            max_items = col_schema.get("maxItems")
            
            if col_name in df.columns:
                # Check first few rows for consistency
                sample = df[col_name].dropna()
                if len(sample) > 0:
                    first_val = sample.iloc[0]
                    if isinstance(first_val, (list, np.ndarray)):
                        length = len(first_val)
                        if min_items is not None and length < min_items:
                            errors.append(f"Column '{col_name}' length {length} < minItems {min_items}")
                        if max_items is not None and length > max_items:
                            errors.append(f"Column '{col_name}' length {length} > maxItems {max_items}")
                    else:
                        errors.append(f"Column '{col_name}' is not a list/array")
    return errors

def validate_record_content(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate content constraints (min/max values)."""
    errors = []
    properties = schema.get("properties", {})
    
    for col_name, col_schema in properties.items():
        if col_name in df.columns:
            if col_schema.get("type") == "number":
                minimum = col_schema.get("minimum")
                maximum = col_schema.get("maximum")
                series = df[col_name]
                
                if minimum is not None and series.min() < minimum:
                    errors.append(f"Column '{col_name}' has values below minimum {minimum}")
                if maximum is not None and series.max() > maximum:
                    errors.append(f"Column '{col_name}' has values above maximum {maximum}")
            elif col_schema.get("type") == "string":
                min_length = col_schema.get("minLength")
                if min_length is not None:
                    # Check string length for non-null values
                    mask = df[col_name].notna()
                    if mask.any():
                        min_len_actual = df.loc[mask, col_name].str.len().min()
                        if min_len_actual < min_length:
                            errors.append(f"Column '{col_name}' has string length {min_len_actual} < min {min_length}")
    return errors

def validate_dataset(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Perform full validation of a DataFrame against a schema."""
    errors = []
    
    errors.extend(validate_column_schema(df, schema))
    errors.extend(validate_fingerprint_dimensions(df, schema))
    errors.extend(validate_record_content(df, schema))
    
    # Check for nulls in required fields
    required = schema.get("required", [])
    for col in required:
        if col in df.columns:
            if df[col].isna().any():
                errors.append(f"Column '{col}' contains null values")
        else:
            # Already caught in column_schema check, but explicit here
            pass
    
    return len(errors) == 0, errors

def validate_sample_row(sample_row: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a single row (dict) against the schema."""
    # Basic type and constraint check without pandas
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Check required keys
    for req in required:
        if req not in sample_row:
            raise ValueError(f"Missing required field: {req}")
    
    # Check types and basic constraints
    for key, value in sample_row.items():
        if key in properties:
            prop = properties[key]
            if prop.get("type") == "string":
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be string")
                if prop.get("minLength") and len(value) < prop["minLength"]:
                    raise ValueError(f"Field '{key}' too short")
            elif prop.get("type") == "number":
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Field '{key}' must be number")
                if prop.get("minimum") is not None and value < prop["minimum"]:
                    raise ValueError(f"Field '{key}' below minimum")
                if prop.get("maximum") is not None and value > prop["maximum"]:
                    raise ValueError(f"Field '{key}' above maximum")
            elif prop.get("type") == "array":
                if not isinstance(value, list):
                    raise ValueError(f"Field '{key}' must be list")
                if prop.get("minItems") and len(value) < prop["minItems"]:
                    raise ValueError(f"Field '{key}' too short")
                if prop.get("maxItems") and len(value) > prop["maxItems"]:
                    raise ValueError(f"Field '{key}' too long")
    
    return True

def validate_output_record(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate an output record (model metrics) against schema."""
    return validate_sample_row(record, schema)

def validate_dataset_file(file_path: Union[str, Path], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Load a dataset file and validate against schema."""
    schema = load_schema(schema_path)
    df = pd.read_parquet(file_path)
    return validate_dataset(df, schema)

def validate_sample_row_from_file(file_path: Union[str, Path], schema_path: Union[str, Path]) -> bool:
    """Load schema and validate a sample row from the file."""
    schema = load_schema(schema_path)
    df = pd.read_parquet(file_path)
    if len(df) == 0:
        raise ValueError("DataFrame is empty")
    sample = df.iloc[0].to_dict()
    return validate_sample_row(sample, schema)

def validate_output_sample(sample: Dict[str, Any], schema_path: Union[str, Path]) -> bool:
    """Validate a sample output object against schema."""
    schema = load_schema(schema_path)
    return validate_output_record(sample, schema)