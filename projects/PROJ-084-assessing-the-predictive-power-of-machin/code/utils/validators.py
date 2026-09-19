import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple
import yaml
import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Dataset Schemas (for reference/completeness based on T007b)
# ---------------------------------------------------------------------

class DatasetRecord(BaseModel):
    smiles: str = Field(..., min_length=1)
    yield_val: float = Field(..., ge=0.0, le=100.0, alias="yield")
    reaction_class: str = Field(..., min_length=1)
    fingerprint_ecfp: List[int] = Field(..., min_length=2048, max_length=2048)
    fingerprint_maccs: List[int] = Field(..., min_length=167, max_length=167)

    class Config:
        populate_by_name = True

class DatasetSchema(BaseModel):
    type: str = Field("object", const=True)
    properties: Dict[str, Any]
    required: List[str]

# ---------------------------------------------------------------------
# Output Schemas (for T008b)
# ---------------------------------------------------------------------

class MetricsRecord(BaseModel):
    R2: float
    RMSE: float
    MAE: float

class SplitRatiosRecord(BaseModel):
    # Flexible dict to allow various split keys (e.g., train, val, test)
    # but we enforce it's a dict of numbers if possible, or just generic object
    pass

    @field_validator('*')
    @classmethod
    def check_numeric(cls, v: Any, info) -> Any:
        # Allow any value but log if it's not numeric for better debugging
        if not isinstance(v, (int, float)):
            logger.warning(f"Split ratio value for {info.field_name} is not numeric: {v}")
        return v

class OutputRecord(BaseModel):
    model_type: str
    hyperparameters: Dict[str, Any]
    metrics: MetricsRecord
    split_ratios: Dict[str, Any]  # Using Dict to match "object" type in schema

class OutputSchema(BaseModel):
    type: str = Field("object", const=True)
    properties: Dict[str, Any]
    required: List[str]

# ---------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_schema(df: pd.DataFrame, schema_props: Dict[str, Any]) -> List[str]:
    """Validate DataFrame columns against schema properties."""
    errors = []
    for col, props in schema_props.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        else:
            # Basic type checking
            dtype = props.get('type')
            if dtype == 'string' and not df[col].dtype == 'object':
                errors.append(f"Column {col} should be string but is {df[col].dtype}")
            elif dtype == 'number':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column {col} should be numeric but is {df[col].dtype}")
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame, col_name: str, expected_len: int) -> List[str]:
    """Validate that a list-column has the expected length."""
    errors = []
    if col_name not in df.columns:
        return [f"Missing column: {col_name}"]
    
    # Check a sample or all rows
    invalid_rows = []
    for idx, val in df[col_name].items():
        if isinstance(val, list) and len(val) != expected_len:
            invalid_rows.append(idx)
    
    if invalid_rows:
        errors.append(f"Column {col_name} has {len(invalid_rows)} rows with length != {expected_len}")
    return errors

def validate_record_content(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a single record (dict) against a schema dict."""
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check types (basic)
    for field, val in record.items():
        if field in properties:
            prop_type = properties[field].get('type')
            if prop_type == 'string' and not isinstance(val, str):
                errors.append(f"Field {field} should be string, got {type(val)}")
            elif prop_type == 'number' and not isinstance(val, (int, float)):
                errors.append(f"Field {field} should be number, got {type(val)}")
            elif prop_type == 'object' and not isinstance(val, dict):
                errors.append(f"Field {field} should be object, got {type(val)}")
            elif prop_type == 'array' and not isinstance(val, list):
                errors.append(f"Field {field} should be array, got {type(val)}")
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Validate a DataFrame against a dataset schema."""
    schema = load_schema(schema_path)
    errors = []
    
    # Validate columns
    col_errors = validate_column_schema(df, schema.get('properties', {}))
    errors.extend(col_errors)
    
    # Validate specific constraints if defined
    # (Simplified for this implementation)
    
    if errors:
        return False, errors
    return True, []

def save_validation_report(errors: List[str], output_path: Union[str, Path]) -> None:
    """Save validation errors to a JSON file."""
    path = Path(output_path)
    report = {
        "status": "failed" if errors else "passed",
        "errors": errors,
        "timestamp": str(pd.Timestamp.now())
    }
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def validate_output_record(record: Dict[str, Any], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validate a single output record (dict) against the output schema.
    Uses Pydantic models for strict validation.
    """
    # Load schema to ensure it exists (optional but good practice)
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        return False, [str(e)]

    errors = []
    try:
        # Map the input dict to the Pydantic model
        # The input dict might have keys like "R2" which map to the model
        # We need to ensure the structure matches OutputRecord
        
        # If the record has a nested "metrics" dict, ensure it matches MetricsRecord
        if 'metrics' in record:
            metrics_data = record['metrics']
            # Validate metrics structure
            try:
                MetricsRecord(**metrics_data)
            except ValidationError as ve:
                for err in ve.errors():
                    errors.append(f"Metrics error: {err['msg']} (field: {err['loc']})")
        
        # Validate split_ratios (loose check, just ensure it's a dict)
        if 'split_ratios' in record:
            if not isinstance(record['split_ratios'], dict):
                errors.append("split_ratios must be a dictionary/object")
        
        # Validate top level
        OutputRecord(**record)
        
    except ValidationError as e:
        for err in e.errors():
            # Format error message
            field = ".".join(str(loc) for loc in err['loc'])
            msg = err['msg']
            errors.append(f"Validation error for '{field}': {msg}")
    
    if errors:
        return False, errors
    return True, []

def validate_dataset_file(file_path: Union[str, Path], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Load a parquet file and validate it against the dataset schema."""
    try:
        df = pd.read_parquet(file_path)
        return validate_dataset(df, schema_path)
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]

def validate_sample_row(sample_data: Dict[str, Any], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validate a sample row (dict) against the dataset schema.
    This is a convenience wrapper for T007b/T008b style validation.
    """
    # Determine if it's dataset or output schema based on content or path
    # For T008b, we specifically expect output schema validation
    if 'metrics' in sample_data or 'model_type' in sample_data:
        return validate_output_record(sample_data, schema_path)
    else:
        # Assume dataset schema
        errors = validate_record_content(sample_data, load_schema(schema_path))
        return (len(errors) == 0), errors