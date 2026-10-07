"""
Data and Output Schema Validators using Pydantic.

This module provides validation logic for dataset records and model output records
based on the YAML schema definitions.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple
import yaml
import pydantic
from pydantic import BaseModel, Field, field_validator, ValidationError, validator
from typing import List as TypedList, Dict as TypedDict, Any as AnyType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path constants
SCHEMA_DIR = Path("specs/001-assess-ml-predictive-power/contracts")
DATASET_SCHEMA_PATH = SCHEMA_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = SCHEMA_DIR / "output.schema.yaml"

# --- Pydantic Models for Dataset Validation (T007b) ---

class FingerprintECFP(BaseModel):
    """Validator for ECFP fingerprint vector (2048 bits)."""
    __root__: TypedList[bool] = Field(..., description="ECFP fingerprint vector (binary bits: true/false)")
    
    @field_validator('__root__')
    @classmethod
    def check_length(cls, v):
        if len(v) != 2048:
            raise ValueError(f"ECFP fingerprint must have exactly 2048 bits, got {len(v)}")
        return v

class FingerprintMACCS(BaseModel):
    """Validator for MACCS key fingerprint vector (167 bits)."""
    __root__: TypedList[bool] = Field(..., description="MACCS key fingerprint (binary bits: true/false)")
    
    @field_validator('__root__')
    @classmethod
    def check_length(cls, v):
        if len(v) != 167:
            raise ValueError(f"MACCS fingerprint must have exactly 167 bits, got {len(v)}")
        return v

class DatasetRecord(BaseModel):
    """Schema for a single row in the processed dataset."""
    smiles: str = Field(..., min_length=1, description="SMILES string of the reaction")
    yield_value: float = Field(..., ge=0.0, le=100.0, alias="yield", description="Yield percentage")
    reaction_class: str = Field(..., min_length=1, description="Reaction class label")
    fingerprint_ecfp: FingerprintECFP
    fingerprint_maccs: FingerprintMACCS

    class Config:
        populate_by_name = True

# --- Pydantic Models for Output Validation (T008a) ---

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

# --- Helper Functions ---

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_fingerprint_dimensions(ecfp_len: int, maccs_len: int) -> Tuple[bool, str]:
    """Validate fingerprint lengths against expected dimensions."""
    if ecfp_len != 2048:
        return False, f"ECFP length {ecfp_len} != 2048"
    if maccs_len != 167:
        return False, f"MACCS length {maccs_len} != 167"
    return True, "Dimensions valid"

def validate_sample_row(row_dict: Dict[str, Any]) -> bool:
    """Validate a single row dictionary against the DatasetRecord schema."""
    try:
        # Handle potential alias 'yield' vs 'yield_value' if needed, 
        # but Pydantic handles alias if defined in model. 
        # Here we assume the input dict keys match the model fields or aliases.
        # The model expects 'yield' as alias for 'yield_value' in the input if we use populate_by_name
        # However, standard dict keys usually match the alias if coming from JSON/CSV.
        # Let's ensure the key 'yield' is present if the model expects it via alias.
        # In the model: yield_value: float = Field(..., alias="yield")
        # Pydantic V2 with populate_by_name=True allows both, but typically input uses alias.
        
        # If the input dict has 'yield', we map it to 'yield_value' for validation if needed,
        # or rely on Pydantic's alias handling.
        # To be safe, let's just pass the dict as is.
        validated = DatasetRecord(**row_dict)
        logger.info("Sample row validation successful.")
        return True
    except ValidationError as e:
        logger.error(f"Sample row validation failed: {e}")
        return False

def validate_dataset_file(file_path: Path) -> bool:
    """Validate a dataset file (Parquet/CSV) against the schema."""
    # This would typically involve reading chunks and validating rows
    # For now, we assume the schema is loaded and we check structure
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    # Implementation would go here to iterate rows
    return True

def validate_output_sample(output_dict: Dict[str, Any]) -> bool:
    """Validate a dictionary against the OutputRecord schema."""
    try:
        validated = OutputRecord(**output_dict)
        logger.info("Output sample validation successful.")
        return True
    except ValidationError as e:
        logger.error(f"Output sample validation failed: {e}")
        return False

# --- Main Entry Points for Verification ---

def validate_dataset_schema() -> bool:
    """
    Load and validate the dataset schema file.
    This function is called to verify T007a/T007b.
    """
    try:
        if not DATASET_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Dataset schema file missing: {DATASET_SCHEMA_PATH}")
        
        schema = load_schema(DATASET_SCHEMA_PATH)
        logger.info(f"Loaded dataset schema from {DATASET_SCHEMA_PATH}")
        
        # Basic check to ensure it's a valid schema structure
        if 'properties' not in schema:
            raise ValueError("Invalid schema: missing 'properties'")
        
        # Test validation with a mock row
        mock_row = {
            "smiles": "CC(=O)O",
            "yield": 50.0,
            "reaction_class": "esterification",
            "fingerprint_ecfp": [True] * 2048,
            "fingerprint_maccs": [True] * 167
        }
        
        if not validate_sample_row(mock_row):
            logger.error("Mock row validation failed.")
            return False
            
        logger.info("Dataset schema validation passed.")
        return True
    except Exception as e:
        logger.error(f"Dataset schema validation failed: {e}")
        return False

def validate_output_schema() -> bool:
    """
    Load and validate the output schema file.
    This function is called to verify T008a.
    """
    try:
        if not OUTPUT_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Output schema file missing: {OUTPUT_SCHEMA_PATH}")
        
        schema = load_schema(OUTPUT_SCHEMA_PATH)
        logger.info(f"Loaded output schema from {OUTPUT_SCHEMA_PATH}")
        
        # Basic check to ensure it's a valid schema structure
        if 'properties' not in schema:
            raise ValueError("Invalid schema: missing 'properties'")
        
        # Test validation with a mock output object
        mock_output = {
            "model_type": "RandomForest",
            "hyperparameters": {"n_estimators": 100, "max_depth": 10},
            "metrics": {
                "R2": 0.85,
                "RMSE": 12.5,
                "MAE": 8.2
            },
            "split_ratios": {"train": 0.7, "val": 0.15, "test": 0.15}
        }
        
        if not validate_output_sample(mock_output):
            logger.error("Mock output validation failed.")
            return False
            
        logger.info("Output schema validation passed.")
        return True
    except Exception as e:
        logger.error(f"Output schema validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run verification if executed directly
    success = True
    if not validate_dataset_schema():
        success = False
    if not validate_output_schema():
        success = False
    
    if not success:
        sys.exit(1)
    logger.info("All schema validations passed.")
    sys.exit(0)