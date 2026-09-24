"""
Schema validation utilities using Pydantic v2 and YAML schemas.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple

import yaml
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.v1 import ValidationError as V1ValidationError

logger = logging.getLogger(__name__)

# --- Pydantic Models for Validation ---

class DatasetRecord(BaseModel):
    """Validation model for a single dataset row."""
    smiles: str = Field(..., min_length=1, description="SMILES string")
    yield_val: float = Field(..., ge=0.0, le=100.0, alias="yield", description="Yield percentage")
    reaction_class: str = Field(..., min_length=1, description="Reaction class")
    fingerprint_ecfp: List[int] = Field(..., min_length=2048, max_length=2048, description="ECFP4 vector")
    fingerprint_maccs: List[int] = Field(..., min_length=167, max_length=167, description="MACCS keys")

    # Rename 'yield' from JSON/YAML to 'yield_val' to avoid Python keyword conflict
    model_config = {"populate_by_name": True}

    @field_validator('fingerprint_ecfp')
    @classmethod
    def check_ecfp_type(cls, v: List[int]) -> List[int]:
        if not all(isinstance(x, int) for x in v):
            raise ValueError("All ECFP items must be integers")
        return v

    @field_validator('fingerprint_maccs')
    @classmethod
    def check_maccs_type(cls, v: List[int]) -> List[int]:
        if not all(isinstance(x, int) for x in v):
            raise ValueError("All MACCS items must be integers")
        return v

class OutputRecord(BaseModel):
    """Validation model for model output metrics."""
    model_type: str = Field(..., min_length=1)
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float] = Field(..., description="Must contain R2, RMSE, MAE")
    split_ratios: Dict[str, float]

    @model_validator(mode='after')
    def check_metrics_keys(self):
        required_keys = {"R2", "RMSE", "MAE"}
        if not required_keys.issubset(self.metrics.keys()):
            raise ValueError(f"Metrics must contain keys: {required_keys}")
        return self

# --- Schema Loading and Validation Functions ---

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_sample_row(row_data: Dict[str, Any], schema_path: Union[str, Path]) -> bool:
    """
    Validate a single row dictionary against the dataset schema.
    Raises ValueError if validation fails.
    """
    try:
        # Map 'yield' key in data to 'yield_val' for Pydantic if necessary
        # The Pydantic model handles aliasing via 'alias="yield"'
        record = DatasetRecord(**row_data)
        logger.debug("Sample row validation successful.")
        return True
    except (V1ValidationError, ValueError) as e:
        logger.error(f"Validation failed for sample row: {e}")
        raise ValueError(f"Dataset schema validation failed: {e}")

def validate_fingerprint_dimensions(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Specifically check fingerprint lengths.
    Returns (is_valid, message).
    """
    ecfp = record.get('fingerprint_ecfp', [])
    maccs = record.get('fingerprint_maccs', [])
    
    if not isinstance(ecfp, list) or len(ecfp) != 2048:
        return False, f"ECFP length is {len(ecfp)}, expected 2048"
    if not isinstance(maccs, list) or len(maccs) != 167:
        return False, f"MACCS length is {len(maccs)}, expected 167"
    
    return True, "Fingerprint dimensions valid"

def validate_dataset_file(
    file_path: Union[str, Path],
    schema_path: Union[str, Path],
    sample_size: int = 10
) -> Dict[str, Any]:
    """
    Load a Parquet/CSV file and validate a sample of rows against the schema.
    Returns a summary report.
    """
    path = Path(file_path)
    schema = load_schema(schema_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    
    logger.info(f"Validating {sample_size} rows from {path} against {schema_path}...")
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    validation_results = []
    errors = []
    
    # Validate sample
    sample_df = df.head(sample_size)
    for idx, row in sample_df.iterrows():
        row_dict = row.to_dict()
        try:
            validate_sample_row(row_dict, schema_path)
            # Extra check for fingerprints
            is_valid, msg = validate_fingerprint_dimensions(row_dict)
            if not is_valid:
                errors.append(f"Row {idx}: {msg}")
            else:
                validation_results.append({"row": idx, "status": "valid"})
        except ValueError as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    return {
        "file": str(path),
        "schema": str(schema_path),
        "sample_size": sample_size,
        "valid_count": len(validation_results),
        "error_count": len(errors),
        "errors": errors
    }

def validate_output_sample(output_data: Dict[str, Any]) -> bool:
    """
    Validate a model output dictionary against the output schema.
    Loads the schema from specs/001-assess-ml-predictive-power/contracts/output.schema.yaml.
    Raises ValueError if validation fails.
    """
    schema_path = Path("specs/001-assess-ml-predictive-power/contracts/output.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Output schema file not found: {schema_path}")
    
    try:
        record = OutputRecord(**output_data)
        logger.debug("Output sample validation successful.")
        return True
    except (V1ValidationError, ValueError) as e:
        logger.error(f"Output validation failed: {e}")
        raise ValueError(f"Output schema validation failed: {e}")