"""
Schema validation utilities for the project.
Validates output data against defined Pydantic models and YAML schemas.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError, root_validator

class ConfigSnapshot(BaseModel):
    """Snapshot of configuration used during execution."""
    hf_api_key: str = Field(..., description="HuggingFace API Key (masked in logs)")
    random_seed: int = Field(..., description="Random seed used")
    max_attempts: int = Field(..., description="Max retry attempts")
    min_valid_functions: int = Field(..., description="Minimum valid functions required")
    batch_size: int = Field(..., description="Batch size for processing")

class Metadata(BaseModel):
    """Metadata about the generated file."""
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0.0"
    pipeline_stage: str

class PairedTTestResult(BaseModel):
    """Result of a paired t-test."""
    statistic: float
    pvalue: float
    alternative: str = "two-sided"

class Statistics(BaseModel):
    """Descriptive statistics for a metric."""
    mean: float
    std: float
    min: float
    max: float
    count: int

class ModelResults(BaseModel):
    """Results of the regression model."""
    coefficients: Dict[str, float]
    adjusted_r_squared: float
    p_values: Dict[str, float]
    vif_filtered_predictors: List[str]

class StatisticalTests(BaseModel):
    """Container for statistical test results."""
    paired_t_test: PairedTTestResult

class OutputSchema(BaseModel):
    """
    Main schema for validation of processed data.
    This represents a single record in the output JSON array.
    """
    code: str
    hash: str
    loc: int
    nesting_depth: int
    param_count: int
    pep8_violations: int
    maintainability_index: float
    docstring_present: bool

    @validator('loc', 'nesting_depth', 'param_count', 'pep8_violations')
    def must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError(f"Field {cls.__name__} must be non-negative")
        return v

    @validator('maintainability_index')
    def maintainability_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("Maintainability index must be between 0 and 100")
        return v

def validate_output(data: List[Dict[str, Any]], file_path: str) -> None:
    """
    Validates a list of dictionaries against the OutputSchema.
    
    Args:
        data: List of dictionaries representing the data rows.
        file_path: Path to the file being validated (for error reporting).
    
    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(data, list):
        raise ValidationError("Root must be a list", model=OutputSchema)
    
    for i, item in enumerate(data):
        try:
            OutputSchema(**item)
        except ValidationError as e:
            raise ValidationError(
                f"Validation failed for item {i} in {file_path}: {e.errors()}",
                model=OutputSchema
            ) from e
    
    # If we get here, all items are valid
    return True
