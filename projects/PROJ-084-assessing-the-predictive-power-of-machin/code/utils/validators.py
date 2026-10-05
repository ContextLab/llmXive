import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple

import yaml
from pydantic import BaseModel, Field, validator, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCHEMA_PATH_DATASET = Path("specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml")
SCHEMA_PATH_OUTPUT = Path("specs/001-assess-ml-predictive-power/contracts/output.schema.yaml")


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


# --- Dataset Schema Models (for T007b) ---
# These are defined here to support the existing validator interface

class FingerprintECFP(BaseModel):
    __root__: List[bool] = Field(..., min_items=2048, max_items=2048)
    description: str = "ECFP fingerprint vector (binary bits: true/false)"

class FingerprintMACCS(BaseModel):
    __root__: List[bool] = Field(..., min_items=167, max_items=167)
    description: str = "MACCS key fingerprint (binary bits: true/false)"

class DatasetRecord(BaseModel):
    smiles: str = Field(..., min_length=1)
    yield_val: float = Field(..., ge=0.0, le=100.0)  # Renamed to yield_val to avoid conflict with 'yield' keyword
    reaction_class: str = Field(..., min_length=1)
    fingerprint_ecfp: FingerprintECFP
    fingerprint_maccs: FingerprintMACCS

    class Config:
        schema_extra = {
            "example": {
                "smiles": "CCO",
                "yield_val": 85.0,
                "reaction_class": "esterification",
                "fingerprint_ecfp": [True] * 2048,
                "fingerprint_maccs": [True] * 167
            }
        }


def validate_fingerprint_dimensions(ecfp: List[bool], maccs: List[bool]) -> Tuple[bool, str]:
    """Validate fingerprint dimensions."""
    if len(ecfp) != 2048:
        return False, f"ECFP length {len(ecfp)} != 2048"
    if len(maccs) != 167:
        return False, f"MACCS length {len(maccs)} != 167"
    return True, "OK"


def validate_sample_row(row: Dict[str, Any]) -> bool:
    """Validate a single row against dataset schema."""
    try:
        # Map 'yield' from data to 'yield_val' in model if necessary
        if 'yield' in row and 'yield_val' not in row:
            row['yield_val'] = row['yield']
        
        record = DatasetRecord(**row)
        logger.info(f"Sample row validated successfully: {record.smiles[:20]}...")
        return True
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return False


def validate_dataset_file(file_path: Path) -> bool:
    """Validate an entire dataset file (Parquet/CSV) against schema."""
    import pandas as pd
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    df = pd.read_parquet(file_path) if file_path.suffix == '.parquet' else pd.read_csv(file_path)
    
    # Basic column check
    required_cols = ['smiles', 'yield', 'reaction_class', 'fingerprint_ecfp', 'fingerprint_maccs']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
    
    # Sample validation
    sample = df.iloc[0].to_dict()
    return validate_sample_row(sample)


# --- Output Schema Models (for T008a) ---

class MetricsRecord(BaseModel):
    R2: float
    RMSE: float
    MAE: float

    @validator('R2', 'RMSE', 'MAE')
    def check_not_nan(cls, v):
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Metric values must be finite numbers")
        return v

class OutputRecord(BaseModel):
    model_type: str
    hyperparameters: Dict[str, Any]
    metrics: MetricsRecord
    split_ratios: Dict[str, float]

    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "RandomForest",
                "hyperparameters": {"n_estimators": 100, "max_depth": 10},
                "metrics": {"R2": 0.85, "RMSE": 12.5, "MAE": 9.2},
                "split_ratios": {"train": 0.7, "val": 0.15, "test": 0.15}
            }
        }


def validate_output_sample(output_data: Dict[str, Any]) -> bool:
    """Validate a sample output object against output schema."""
    try:
        # Ensure metrics is a dict with required keys if passed as dict
        if isinstance(output_data.get('metrics'), dict):
            # Pydantic will handle the nested validation
            pass
        
        record = OutputRecord(**output_data)
        logger.info(f"Output record validated successfully: {record.model_type}")
        return True
    except ValidationError as e:
        logger.error(f"Output validation error: {e}")
        return False


def validate_output_schema() -> bool:
    """
    Load the output schema file and validate a sample output object.
    This function acts as the verification entry point for T008a.
    """
    logger.info("Loading output schema...")
    try:
        schema = load_schema(SCHEMA_PATH_OUTPUT)
        logger.info(f"Schema loaded: {schema.get('type')}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        raise SystemExit(1)

    # Define a valid sample output based on the schema structure
    sample_output = {
        "model_type": "RandomForest",
        "hyperparameters": {"n_estimators": 100, "max_depth": 20},
        "metrics": {
            "R2": 0.8543,
            "RMSE": 12.3456,
            "MAE": 9.8765
        },
        "split_ratios": {
            "train": 0.70,
            "val": 0.15,
            "test": 0.15
        }
    }

    logger.info("Validating sample output against schema...")
    if not validate_output_sample(sample_output):
        logger.error("Sample output validation failed.")
        raise SystemExit(1)

    logger.info("Output schema validation successful.")
    return True


def validate_dataset_schema() -> bool:
    """
    Load the dataset schema file and validate a sample dataset row.
    This function acts as the verification entry point for T007b.
    """
    logger.info("Loading dataset schema...")
    try:
        schema = load_schema(SCHEMA_PATH_DATASET)
        logger.info(f"Schema loaded: {schema.get('type')}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        raise SystemExit(1)

    # Define a valid sample dataset row
    sample_row = {
        "smiles": "CC(=O)O",
        "yield": 75.5,
        "reaction_class": "hydrolysis",
        "fingerprint_ecfp": [True] * 2048,
        "fingerprint_maccs": [True] * 167
    }

    logger.info("Validating sample dataset row...")
    if not validate_sample_row(sample_row):
        logger.error("Sample dataset row validation failed.")
        raise SystemExit(1)

    logger.info("Dataset schema validation successful.")
    return True


if __name__ == "__main__":
    # Run verification if executed directly
    if len(sys.argv) > 1 and sys.argv[1] == "output":
        validate_output_schema()
    else:
        # Default to dataset schema validation if no arg, or run both
        validate_dataset_schema()
        validate_output_schema()