import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
import pandas as pd
import yaml

try:
    from pydantic import BaseModel, Field, field_validator, ValidationError
    from pydantic_settings import BaseSettings
except ImportError:
    raise ImportError("pydantic and pydantic-settings are required for validation. Install with: pip install pydantic pydantic-settings")

# --- Dataset Schema Models (from T007b) ---

class DatasetRecord(BaseModel):
    smiles: str
    yield_: float = Field(..., alias="yield", ge=0.0, le=100.0)
    reaction_class: str
    fingerprint_ecfp: List[int]
    fingerprint_maccs: List[int]

    class Config:
        populate_by_name = True

class DatasetSchema(BaseModel):
    fields: Dict[str, Any]

# --- Output Schema Models (T008b Implementation) ---

class MetricsRecord(BaseModel):
    R2: float
    RMSE: float
    MAE: float

class SplitRatiosRecord(BaseModel):
    train: float
    validation: float
    test: float

class OutputRecord(BaseModel):
    model_type: str
    hyperparameters: Dict[str, Any]
    metrics: MetricsRecord
    split_ratios: SplitRatiosRecord

class OutputSchema(BaseModel):
    model_type: Any
    hyperparameters: Any
    metrics: Any
    split_ratios: Any

# --- Utility Functions ---

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition file.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate DataFrame columns against a schema definition.
    Returns a list of error messages.
    """
    errors = []
    expected_fields = schema.get('fields', schema) # Handle both dict of fields or direct field defs
    
    if not isinstance(expected_fields, dict):
        errors.append("Invalid schema format: expected 'fields' key or direct field definitions")
        return errors

    for col_name, col_def in expected_fields.items():
        if col_name not in df.columns:
            errors.append(f"Missing column: {col_name}")
        else:
            # Basic type checking could be added here if schema defines types strictly
            pass
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame) -> List[str]:
    """
    Validate fingerprint dimensions (ECFP=2048, MACCS=167).
    """
    errors = []
    
    if 'fingerprint_ecfp' in df.columns:
        # Check first row length as a sample (assuming uniformity)
        if not df['fingerprint_ecfp'].empty:
            sample = df['fingerprint_ecfp'].iloc[0]
            if isinstance(sample, list) and len(sample) != 2048:
                errors.append(f"fingerprint_ecfp length is {len(sample)}, expected 2048")
    
    if 'fingerprint_maccs' in df.columns:
        if not df['fingerprint_maccs'].empty:
            sample = df['fingerprint_maccs'].iloc[0]
            if isinstance(sample, list) and len(sample) != 167:
                errors.append(f"fingerprint_maccs length is {len(sample)}, expected 167")
    
    return errors

def validate_record_content(record: Dict[str, Any], schema_class: Type[BaseModel]) -> List[str]:
    """
    Validate a dictionary record against a Pydantic model.
    """
    errors = []
    try:
        schema_class(**record)
    except ValidationError as e:
        for error in e.errors():
            errors.append(f"Validation error: {'.'.join(map(str, error['loc']))}: {error['msg']}")
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Full validation of a dataset against a schema file.
    """
    schema = load_schema(schema_path)
    errors = []
    
    # Column validation
    errors.extend(validate_column_schema(df, schema))
    
    # Fingerprint validation
    errors.extend(validate_fingerprint_dimensions(df))
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }

def validate_output_file(file_path: Union[str, Path], schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate an output JSON/Parquet file against the output schema.
    This function specifically handles the OutputRecord structure.
    """
    path = Path(file_path)
    errors = []
    
    if not path.exists():
        return {
            "valid": False,
            "errors": [f"File not found: {path}"],
            "timestamp": datetime.now().isoformat()
        }

    # Load schema to ensure it matches expected structure (optional deep check)
    try:
        schema_def = load_schema(schema_path)
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to load schema: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        }

    # Try to load and validate the file content
    try:
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix == '.parquet':
            # For parquet, we assume it might contain a list of records or a single record in a specific column
            # For this task, we assume the output is a JSON file or a simple dict structure for metrics
            # If it's a dataframe, we take the first row if it's a single record result
            df = pd.read_parquet(path)
            if len(df) > 0:
                # Convert first row to dict
                data = df.iloc[0].to_dict()
            else:
                return {
                    "valid": False,
                    "errors": ["Parquet file is empty"],
                    "timestamp": datetime.now().isoformat()
                }
        else:
            return {
                "valid": False,
                "errors": [f"Unsupported file format: {path.suffix}"],
                "timestamp": datetime.now().isoformat()
            }

        # Validate against Pydantic model
        validation_errors = validate_record_content(data, OutputRecord)
        errors.extend(validation_errors)

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }

def validate_dataset_file(file_path: Union[str, Path], schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate a dataset file (Parquet/CSV) against a dataset schema.
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "valid": False,
            "errors": [f"File not found: {path}"],
            "timestamp": datetime.now().isoformat()
        }

    try:
        if path.suffix == '.parquet':
            df = pd.read_parquet(path)
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
        else:
            return {
                "valid": False,
                "errors": [f"Unsupported file format: {path.suffix}"],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to read file: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        }

    return validate_dataset(df, schema_path)

def save_validation_report(report: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Save a validation report to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)