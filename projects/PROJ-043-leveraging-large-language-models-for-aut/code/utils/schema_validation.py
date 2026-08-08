"""
Schema validation utilities using Pydantic.

This module provides Pydantic models to validate configuration and output data
against the definitions in contracts/config.schema.yaml and contracts/output.schema.yaml.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator, ValidationError
import yaml
import os
from pathlib import Path

# --- Configuration Schema ---

class ConfigSchema(BaseModel):
    """Pydantic model for validating application configuration."""
    HF_API_KEY: str = Field(..., description="Hugging Face API key")
    RANDOM_SEED: int = Field(..., ge=0, description="Random seed")
    MAX_ATTEMPTS: int = Field(..., ge=1, description="Max retry attempts")
    MIN_VALID_FUNCTIONS: int = Field(..., ge=1, description="Min valid functions")
    BATCH_SIZE: int = Field(..., ge=1, description="Batch size")

    @validator('HF_API_KEY')
    def check_api_key(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('HF_API_KEY must be a non-empty string')
        return v

# --- Output Schema ---

class MetricRecord(BaseModel):
    """Schema for individual metric calculation."""
    loc: int = Field(..., ge=0)
    max_nesting: int = Field(..., ge=0)
    param_count: int = Field(..., ge=0)
    has_docstring: bool
    cyclomatic_complexity: float
    pylint_score: float

class DeltaRecord(BaseModel):
    """Schema for metric deltas."""
    complexity_delta: float
    pylint_delta: float
    maintainability_delta: float

class OutputRecord(BaseModel):
    """Schema for a single record in the output dataset."""
    function_hash: str
    original_code: str
    metrics: MetricRecord
    refactored_code: Optional[str] = None
    baseline_code: Optional[str] = None
    deltas: Optional[DeltaRecord] = None
    status: str = Field(..., pattern="^(success|failed|skipped)$")

class OutputMetadata(BaseModel):
    """Schema for output metadata."""
    version: str
    timestamp: str
    source_dataset: str

class OutputSchema(BaseModel):
    """Pydantic model for validating pipeline output."""
    metadata: OutputMetadata
    records: List[OutputRecord]

    @validator('records')
    def check_records_not_empty(cls, v):
        if not v:
            raise ValueError('Output records list cannot be empty')
        return v

# --- Validation Helpers ---

def validate_config(data: Dict[str, Any]) -> ConfigSchema:
    """
    Validates configuration data against the ConfigSchema.
    
    Args:
        data: Dictionary containing configuration values.
        
    Returns:
        Validated ConfigSchema instance.
        
    Raises:
        ValidationError: If data does not conform to schema.
    """
    return ConfigSchema(**data)

def validate_output(data: Dict[str, Any]) -> OutputSchema:
    """
    Validates output data against the OutputSchema.
    
    Args:
        data: Dictionary containing output data.
        
    Returns:
        Validated OutputSchema instance.
        
    Raises:
        ValidationError: If data does not conform to schema.
    """
    return OutputSchema(**data)

def validate_yaml_schema(yaml_path: str, data: Dict[str, Any]) -> bool:
    """
    Optional: Load schema from YAML file and validate data.
    Currently uses Pydantic models directly as the source of truth,
    but this function bridges the gap if YAML definitions need to be
    dynamically loaded in the future.
    
    Args:
        yaml_path: Path to the YAML schema definition.
        data: Data to validate.
        
    Returns:
        True if validation passes.
    """
    # In this implementation, the Pydantic models ARE the schema.
    # This function serves as a hook if dynamic YAML validation is required later.
    # For now, it simply attempts to load the YAML to ensure it exists and is valid syntax.
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {yaml_path}")
    
    with open(path, 'r') as f:
        schema_def = yaml.safe_load(f)
    
    # If we wanted to use jsonschema here, we would do:
    # from jsonschema import validate
    # validate(instance=data, schema=schema_def)
    
    return True

def validate_config_from_env() -> ConfigSchema:
    """
    Loads configuration from environment variables and validates it.
    
    Returns:
        Validated ConfigSchema.
    """
    env_vars = {
        'HF_API_KEY': os.getenv('HF_API_KEY'),
        'RANDOM_SEED': int(os.getenv('RANDOM_SEED', '42')),
        'MAX_ATTEMPTS': int(os.getenv('MAX_ATTEMPTS', '5')),
        'MIN_VALID_FUNCTIONS': int(os.getenv('MIN_VALID_FUNCTIONS', '100')),
        'BATCH_SIZE': int(os.getenv('BATCH_SIZE', '10'))
    }
    return validate_config(env_vars)
