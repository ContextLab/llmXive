"""
Schema validation module using Pydantic for configuration and output validation.

This module provides Pydantic models that correspond to the YAML schemas
defined in contracts/config.schema.yaml and contracts/output.schema.yaml.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError, root_validator
import yaml
import os
from pathlib import Path
from datetime import datetime
import uuid


# --- Configuration Schema Models ---

class ConfigSchema(BaseModel):
    """Pydantic model for validating runtime configuration."""
    
    HF_API_KEY: str = Field(..., min_length=20, description="Hugging Face API key")
    RANDOM_SEED: int = Field(default=42, ge=0, description="Random seed")
    MAX_ATTEMPTS: int = Field(default=400, ge=1, description="Max retry attempts")
    MIN_VALID_FUNCTIONS: int = Field(default=100, ge=1, description="Min valid functions")
    BATCH_SIZE: int = Field(default=10, ge=1, le=20, description="Batch size")
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    CACHE_DIR: str = Field(default="data/cache")
    OUTPUT_DIR: str = Field(default="data/processed")
    
    class Config:
        arbitrary_types_allowed = True
        
    @validator('HF_API_KEY')
    def validate_api_key(cls, v):
        if not v.startswith("hf_"):
            raise ValueError("HF_API_KEY must start with 'hf_'")
        return v


# --- Output Schema Models ---

class ConfigSnapshot(BaseModel):
    """Snapshot of configuration used for the run."""
    random_seed: int
    max_attempts: int
    min_valid_functions: int
    batch_size: int
    log_level: str
    
class Metadata(BaseModel):
    """Metadata about the pipeline run."""
    run_id: str = Field(..., description="Unique run identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    total_functions: int = Field(..., ge=0)
    valid_functions: int = Field(..., ge=0)
    model_version: str = Field(default="WizardCoder-Python-13B")
    config_snapshot: Optional[ConfigSnapshot] = None
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid ISO 8601 timestamp format")
        return v
        
    @root_validator
    def validate_counts(cls, values):
        total = values.get('total_functions', 0)
        valid = values.get('valid_functions', 0)
        if valid > total:
            raise ValueError("valid_functions cannot exceed total_functions")
        return values


class OLSResults(BaseModel):
    """OLS regression results."""
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    adjusted_r_squared: float
    f_statistic: float
    f_p_value: float
    
    @validator('adjusted_r_squared')
    def validate_r_squared(cls, v):
        if not (-1.0 <= v <= 1.0):
            raise ValueError("Adjusted R-squared must be between -1 and 1")
        return v


class RidgeResults(BaseModel):
    """Ridge regression results."""
    coefficients: Dict[str, float]
    alpha: float = Field(..., gt=0)
    
class GLMResults(BaseModel):
    """GLM results."""
    coefficients: Dict[str, float]
    family: str = Field(default="Gaussian")
    
class ModelResults(BaseModel):
    """Results from statistical modeling."""
    ols: OLSResults
    ridge: Optional[RidgeResults] = None
    glm: Optional[GLMResults] = None
    
class TTestResult(BaseModel):
    """Generic t-test result."""
    t_statistic: float
    p_value: float
    significant: bool = Field(..., description="Whether p < 0.05")
    
class PairedTTestResult(TTestResult):
    """Paired t-test results."""
    confidence_interval: List[float] = Field(..., min_items=2, max_items=2)
    
class OneSampleTTestResult(TTestResult):
    """One-sample t-test results."""
    mean_difference: float
    
class StatisticalTests(BaseModel):
    """Results from statistical hypothesis tests."""
    paired_t_test: Optional[PairedTTestResult] = None
    one_sample_t_test: Optional[OneSampleTTestResult] = None
    
class CrossValidationResults(BaseModel):
    """K-fold cross-validation results."""
    k_folds: int = Field(..., ge=2)
    mean_coefficients: Dict[str, float]
    std_coefficients: Dict[str, float]
    mean_r_squared: float
    
class Summary(BaseModel):
    """High-level summary of findings."""
    primary_conclusion: str
    significant_predictors: List[str] = Field(default_factory=list)
    refactoring_effectiveness: str = Field(..., pattern="^(SIGNIFICANT|NOT_SIGNIFICANT|INCONCLUSIVE)$")
    
class OutputSchema(BaseModel):
    """Pydantic model for validating final output."""
    metadata: Metadata
    model_results: ModelResults
    statistical_tests: Optional[StatisticalTests] = None
    cross_validation: Optional[CrossValidationResults] = None
    summary: Summary
    
    class Config:
        arbitrary_types_allowed = True


# --- Validation Functions ---

def validate_config(config_dict: Dict[str, Any]) -> ConfigSchema:
    """
    Validate a configuration dictionary against the ConfigSchema.
    
    Args:
        config_dict: Dictionary containing configuration values
        
    Returns:
        Validated ConfigSchema instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return ConfigSchema(**config_dict)
    except ValidationError as e:
        raise ValidationError(f"Configuration validation failed: {e}")
        

def validate_output(output_dict: Dict[str, Any]) -> OutputSchema:
    """
    Validate an output dictionary against the OutputSchema.
    
    Args:
        output_dict: Dictionary containing output data
        
    Returns:
        Validated OutputSchema instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return OutputSchema(**output_dict)
    except ValidationError as e:
        raise ValidationError(f"Output validation failed: {e}")
        

def validate_yaml_schema(schema_path: str) -> bool:
    """
    Validate that a YAML schema file is syntactically correct.
    
    Args:
        schema_path: Path to the YAML schema file
        
    Returns:
        True if valid, raises exception otherwise
    """
    try:
        with open(schema_path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML schema at {schema_path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        

def validate_config_from_env() -> ConfigSchema:
    """
    Validate configuration by loading values from environment variables.
    
    Returns:
        Validated ConfigSchema instance
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    config_dict = {
        'HF_API_KEY': os.getenv('HF_API_KEY'),
        'RANDOM_SEED': int(os.getenv('RANDOM_SEED', 42)),
        'MAX_ATTEMPTS': int(os.getenv('MAX_ATTEMPTS', 400)),
        'MIN_VALID_FUNCTIONS': int(os.getenv('MIN_VALID_FUNCTIONS', 100)),
        'BATCH_SIZE': int(os.getenv('BATCH_SIZE', 10)),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'CACHE_DIR': os.getenv('CACHE_DIR', 'data/cache'),
        'OUTPUT_DIR': os.getenv('OUTPUT_DIR', 'data/processed'),
    }
    
    return validate_config(config_dict)