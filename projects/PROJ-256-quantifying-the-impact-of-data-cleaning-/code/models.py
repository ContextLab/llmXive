from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ImputationMethod(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    KNN = "knn"
    MODE = "mode"

class CleaningStrategyType(str, Enum):
    OUTLIER_REMOVAL = "outlier_removal"
    IMPUTATION = "imputation"
    RECODING = "recoding"
    COMBINED = "combined"

class Dataset(BaseModel):
    name: str
    path: str
    rows: int
    columns: int
    checksum: str
    missing_rate: float

class CleaningStrategy(BaseModel):
    type: CleaningStrategyType
    parameters: Dict[str, Any]
    description: str

class AnalysisResult(BaseModel):
    dataset_name: str
    strategy_used: Optional[str] = None
    p_value: float
    ci_lower: float
    ci_upper: float
    effect_size: float
    test_type: str  # e.g., "t_test", "linear_regression"
    coefficients: Optional[List[float]] = None

class ComparisonReport(BaseModel):
    """
    The core entity for T040.
    Contains baseline metrics, cleaned metrics, diffs, and sensitivity analysis.
    """
    metadata: Dict[str, Any] = Field(default_factory=dict)
    comparison: Dict[str, Any] = Field(default_factory=dict)
    sensitivity_analysis: Optional[Dict[str, Any]] = None

    @field_validator('comparison')
    def validate_comparison_structure(cls, v):
        required_keys = ['baseline', 'cleaned', 'absolute_diff', 'relative_diff', 'summary']
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Missing required key in comparison: {key}")
        return v

def main():
    """Entry point for models module if run directly."""
    pass
