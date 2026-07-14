"""
Data models and entities for the Quantifying Impact of Data Cleaning project.
Defines Pydantic models for Dataset, CleaningStrategy, AnalysisResult, and ComparisonReport.
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
    RECODING = "recoding"

class Dataset(BaseModel):
    dataset_id: str
    dataset_name: str
    source_url: Optional[str] = None
    checksum: Optional[str] = None
    row_count: int
    column_count: int
    missing_rate: float

class CleaningStrategy(BaseModel):
    """Defines a cleaning strategy to be applied."""
    strategy_type: CleaningStrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str

class AnalysisResult(BaseModel):
    dataset_id: str
    test_type: str  # e.g., "t_test", "regression"
    p_value: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    effect_size: Optional[float] = None
    r_squared: Optional[float] = None
    coefficients: Optional[List[float]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ComparisonReport(BaseModel):
    report_id: str
    created_at: str
    baseline_metrics: Dict[str, Any]
    cleaned_metrics: Dict[str, Any]
    absolute_diff: List[float]
    relative_diff: List[float]
    comparison_details: Optional[List[Dict[str, Any]]] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    file_checksum: Optional[str] = None

    @field_validator('created_at')
    @classmethod
    def check_created_at(cls, v):
        if not v:
            raise ValueError('created_at is required')
        return v
