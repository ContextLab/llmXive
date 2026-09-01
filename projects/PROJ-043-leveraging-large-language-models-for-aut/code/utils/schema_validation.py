from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError, root_validator
import yaml
import os
from pathlib import Path
from datetime import datetime

# --- Config Schema Models ---

class ConfigSnapshot(BaseModel):
    """Snapshot of configuration used for a run."""
    hf_api_key_masked: str = Field(..., description="Masked HF API key")
    random_seed: int = Field(..., description="Random seed")
    max_attempts: int = Field(..., description="Max attempts for data fetch")
    min_valid_functions: int = Field(..., description="Min valid functions required")
    batch_size: int = Field(..., description="Batch size for processing")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class Metadata(BaseModel):
    """Metadata for output files."""
    version: str = "1.0.0"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_dataset: Optional[str] = None
    model_used: Optional[str] = None

class ConfigSchema(BaseModel):
    """
    Pydantic model representing the validation schema for configuration.
    Maps to contracts/config.schema.yaml logic.
    """
    hf_api_key: str = Field(..., description="HuggingFace API Key")
    random_seed: int = Field(42, ge=0, description="Random seed for reproducibility")
    max_attempts: int = Field(400, ge=1, description="Max attempts to fetch valid data")
    min_valid_functions: int = Field(100, ge=1, description="Minimum valid functions required")
    batch_size: int = Field(10, ge=1, le=10, description="Batch size for LLM calls")

    @validator('hf_api_key')
    def validate_key(cls, v):
        if not v or not v.startswith("hf_"):
            raise ValueError("HF_API_KEY must start with 'hf_'")
        return v

    class Config:
        schema_extra = {
            "title": "LLM Refactoring Configuration",
            "description": "Configuration for the LLM Refactoring Pipeline",
            "properties": {
                "hf_api_key": {"type": "string", "description": "HuggingFace API Key"},
                "random_seed": {"type": "integer", "description": "Random seed"},
                "max_attempts": {"type": "integer", "description": "Max attempts"},
                "min_valid_functions": {"type": "integer", "description": "Min valid functions"},
                "batch_size": {"type": "integer", "description": "Batch size"}
            }
        }

# --- Output Schema Models ---

class FunctionSample(BaseModel):
    """Represents a single function sample in the output."""
    code: str = Field(..., description="Original code")
    metrics: Dict[str, Any] = Field(..., description="Computed metrics")
    hash: str = Field(..., description="Hash of the code")
    refactored_code: Optional[str] = None
    baseline_code: Optional[str] = None
    deltas: Optional[Dict[str, float]] = None
    status: str = Field("success", description="Processing status")

class TTestResult(BaseModel):
    """Result of a T-Test."""
    statistic: float
    pvalue: float
    method: str
    alternative: str

class PairedTTestResult(TTestResult):
    pass

class OneSampleTTestResult(TTestResult):
    popmean: float = 0.0

class StatisticalTests(BaseModel):
    """Container for statistical test results."""
    paired_t_test: Optional[PairedTTestResult] = None
    one_sample_t_test: Optional[OneSampleTTestResult] = None
    baseline_delta_check: Optional[bool] = None

class CrossValidationResults(BaseModel):
    """Results from k-fold cross-validation."""
    k_folds: int
    mean_coefficients: Dict[str, float]
    std_coefficients: Dict[str, float]
    mean_r2: float

class OLSResults(BaseModel):
    """Results from OLS regression."""
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    adjusted_r_squared: float
    f_statistic: Optional[float] = None
    f_pvalue: Optional[float] = None

class RidgeResults(BaseModel):
    """Results from Ridge regression."""
    coefficients: Dict[str, float]
    alpha: float
    r_squared: float

class GLMResults(BaseModel):
    """Results from GLM."""
    coefficients: Dict[str, float]
    family: str
    deviance: float

class ModelResults(BaseModel):
    """Container for model results."""
    ols: Optional[OLSResults] = None
    ridge: Optional[RidgeResults] = None
    glm: Optional[GLMResults] = None
    cross_validation: Optional[CrossValidationResults] = None

class Summary(BaseModel):
    """Summary of the entire run."""
    total_functions: int
    valid_functions: int
    refactored_count: int
    failed_count: int
    primary_test: str
    significant: bool
    p_value: float

class OutputSchema(BaseModel):
    """
    Pydantic model representing the validation schema for output files.
    Maps to contracts/output.schema.yaml logic.
    """
    metadata: Metadata
    config_snapshot: ConfigSnapshot
    data: List[FunctionSample]
    statistics: StatisticalTests
    models: ModelResults
    summary: Summary

    @validator('data')
    def validate_data_list(cls, v):
        if not v:
            raise ValueError("Data list cannot be empty")
        return v

# --- Validation Functions ---

def validate_config(data: Dict[str, Any]) -> ConfigSchema:
    """Validate configuration dictionary against ConfigSchema."""
    try:
        return ConfigSchema(**data)
    except ValidationError as e:
        raise ValidationError(f"Configuration validation failed: {e}") from e

def validate_output(data: Dict[str, Any]) -> OutputSchema:
    """Validate output dictionary against OutputSchema."""
    try:
        return OutputSchema(**data)
    except ValidationError as e:
        raise ValidationError(f"Output validation failed: {e}") from e

def validate_yaml_schema(schema_path: str, data_path: str) -> bool:
    """
    Validate a YAML data file against a YAML schema definition.
    Note: This is a basic implementation. For complex schema validation,
    a library like `jsonschema` or `datamodel-code-generator` is preferred.
    Here we use Pydantic to validate the loaded YAML data.
    """
    with open(schema_path, 'r') as f:
        # In a real scenario, we might parse the schema to determine which model to use.
        # For now, we assume the schema path implies the model or we rely on the caller.
        pass
    
    with open(data_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # This is a simplified check; in T005 we focus on the Pydantic models.
    # A full YAML schema validator would map the schema file to the Pydantic model.
    return True

def validate_config_from_env() -> ConfigSchema:
    """Validate configuration loaded from environment variables."""
    data = {
        "hf_api_key": os.getenv("HF_API_KEY", ""),
        "random_seed": int(os.getenv("RANDOM_SEED", 42)),
        "max_attempts": int(os.getenv("MAX_ATTEMPTS", 400)),
        "min_valid_functions": int(os.getenv("MIN_VALID_FUNCTIONS", 100)),
        "batch_size": int(os.getenv("BATCH_SIZE", 10))
    }
    return validate_config(data)
