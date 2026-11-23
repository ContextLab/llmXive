import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError, root_validator

class ConfigSnapshot(BaseModel):
    hf_api_key_used: bool
    random_seed: int
    max_attempts: int
    min_valid_functions: int
    target_valid_functions: int
    batch_size: int
    baseline_tolerance: float

class Metadata(BaseModel):
    timestamp: str
    version: str = "1.0.0"
    pipeline_stage: str

class Statistics(BaseModel):
    mean: float
    std: float
    count: int

class PairedTTestResult(BaseModel):
    statistic: float
    pvalue: float
    confidence_interval: Optional[tuple] = None

class ModelResults(BaseModel):
    model_type: str
    coefficients: Dict[str, float]
    r_squared: float
    adjusted_r_squared: float

class StatisticalTests(BaseModel):
    t_test: PairedTTestResult

class OutputSchema(BaseModel):
    metadata: Metadata
    config_snapshot: ConfigSnapshot
    data: List[Dict[str, Any]]
    statistics: Optional[Statistics] = None
    model_results: Optional[List[ModelResults]] = None
    statistical_tests: Optional[StatisticalTests] = None

def validate_output(data: Dict[str, Any]) -> OutputSchema:
    """
    Validate the output data against the OutputSchema.
    """
    try:
        return OutputSchema(**data)
    except ValidationError as e:
        raise ValueError(f"Output validation failed: {e}")
