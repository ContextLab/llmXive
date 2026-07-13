"""
Data models and entities for the project.
Defines schemas for Dataset, CleaningStrategy, AnalysisResult, and ComparisonReport.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ImputationMethod(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    KNN = "knn"

class CleaningStrategyType(str, Enum):
    OUTLIER_REMOVAL = "outlier_removal"
    IMPUTATION = "imputation"
    CATEGORICAL_RECODING = "categorical_recoding"
    COMBINED = "combined"

class Dataset(BaseModel):
    name: str
    source: str
    checksum: Optional[str] = None
    n_rows: Optional[int] = None
    n_cols: Optional[int] = None
    missing_rate: Optional[float] = None

class CleaningStrategy(BaseModel):
    type: CleaningStrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

class AnalysisResult(BaseModel):
    dataset_name: str
    strategy: Optional[str] = None
    test_type: str
    p_value: float
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None
    ci_width: Optional[float] = None
    effect_size: Optional[float] = None
    effect_size_type: Optional[str] = None
    significance: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ComparisonReport(BaseModel):
    id: str
    created_at: str
    baseline_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    cleaned_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('created_at')
    @classmethod
    def validate_created_at(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("created_at must be a valid ISO 8601 datetime string")
        return v
