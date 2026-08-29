"""
Validators for dataset and model output schemas.
Uses Pydantic for robust schema definition and validation.
"""
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


# --- Dataset Schema Models ---

class DatasetRecord(BaseModel):
    """Schema for a single record in the dataset."""
    smiles: str = Field(..., description="SMILES string of the reaction")
    yield_pct: float = Field(..., ge=0.0, le=100.0, description="Reaction yield percentage")
    reaction_class: str = Field(..., description="Class of the reaction")
    fingerprint_ecfp: List[int] = Field(
        ...,
        min_length=2048,
        max_length=2048,
        description="ECFP4 fingerprint vector"
    )
    fingerprint_maccs: List[int] = Field(
        ...,
        min_length=167,
        max_length=167,
        description="MACCS keys fingerprint vector"
    )


class DatasetSchema(BaseModel):
    """Schema for the entire dataset validation."""
    records: List[DatasetRecord]

    @field_validator('records')
    @classmethod
    def validate_all_records(cls, v: List[DatasetRecord]) -> List[DatasetRecord]:
        if not v:
            raise ValueError("Dataset must contain at least one record")
        return v


# --- Output Schema Models ---

class MetricsRecord(BaseModel):
    """Schema for model performance metrics."""
    R2: float = Field(..., description="R-squared coefficient")
    RMSE: float = Field(..., ge=0.0, description="Root Mean Squared Error")
    MAE: float = Field(..., ge=0.0, description="Mean Absolute Error")


class OutputRecord(BaseModel):
    """Schema for a single model output artifact."""
    model_type: str = Field(..., description="Type of model")
    hyperparameters: Dict[str, Any] = Field(..., description="Hyperparameters used")
    metrics: MetricsRecord
    split_ratios: Dict[str, float] = Field(
        ...,
        description="Ratios of train/val/test splits"
    )

    @model_validator(mode='after')
    def validate_split_ratios_sum(self) -> 'OutputRecord':
        """Ensure split ratios sum to 1.0 (with tolerance)."""
        ratios = self.split_ratios
        total = sum(ratios.values())
        if not abs(total - 1.0) < 1e-6:
            raise ValueError(
                f"Split ratios must sum to 1.0, got {total:.6f} for {ratios}"
            )
        return self


class OutputSchema(BaseModel):
    """Schema for the model output validation."""
    results: List[OutputRecord]

    @field_validator('results')
    @classmethod
    def validate_all_results(cls, v: List[OutputRecord]) -> List[OutputRecord]:
        if not v:
            raise ValueError("Output must contain at least one result record")
        return v


# --- Helper Functions ---

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    Note: This is primarily for documentation or fallback validation.
    Primary validation is done via Pydantic models above.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_dataset_file(
    file_path: Union[str, Path],
    schema_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Validate a dataset file (Parquet/CSV) against the dataset schema.
    
    Args:
        file_path: Path to the data file
        schema_path: Optional path to schema YAML (for logging/reference)
        
    Returns:
        Dict with validation status and details
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    
    logger.info(f"Validating dataset: {path}")
    
    # Load data
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Validate using Pydantic
    validation_errors = []
    valid_count = 0
    
    # Convert to records and validate
    # Note: For large datasets, we might want to sample or batch
    # Here we validate the whole set for correctness
    try:
        # Convert dataframe to list of dicts
        records_data = df.to_dict('records')
        
        # Validate each record
        for i, record_data in enumerate(records_data):
            try:
                # Handle potential key mismatch (e.g., 'yield' vs 'yield_pct')
                if 'yield' in record_data and 'yield_pct' not in record_data:
                    record_data['yield_pct'] = record_data.pop('yield')
                
                record = DatasetRecord(**record_data)
                valid_count += 1
            except ValidationError as e:
                validation_errors.append({
                    "row_index": i,
                    "errors": str(e)
                })
                
        status = "valid" if not validation_errors else "invalid"
        
        return {
            "status": status,
            "file": str(path),
            "total_records": len(records_data),
            "valid_records": valid_count,
            "invalid_records": len(validation_errors),
            "errors": validation_errors[:10]  # Limit error output
        }
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return {
            "status": "error",
            "file": str(path),
            "error": str(e)
        }


def validate_output_file(
    file_path: Union[str, Path],
    schema_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Validate a model output JSON file against the output schema.
    
    Args:
        file_path: Path to the JSON output file
        schema_path: Optional path to schema YAML (for logging/reference)
        
    Returns:
        Dict with validation status and details
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Output file not found: {path}")
    
    logger.info(f"Validating output: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate using Pydantic
        # The JSON structure might be a single record or a list
        # We assume it matches OutputSchema (list of records)
        
        # If it's a single record, wrap it
        if isinstance(data, dict) and 'results' not in data:
            # Assume it's a single result, wrap in a list
            data = {"results": [data]}
        
        validation_result = OutputSchema(**data)
        
        return {
            "status": "valid",
            "file": str(path),
            "results_count": len(validation_result.results)
        }
        
    except ValidationError as e:
        return {
            "status": "invalid",
            "file": str(path),
            "errors": str(e)
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "file": str(path),
            "error": f"Invalid JSON: {e}"
        }
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return {
            "status": "error",
            "file": str(path),
            "error": str(e)
        }


def save_validation_report(report: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """Save a validation report to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {path}")