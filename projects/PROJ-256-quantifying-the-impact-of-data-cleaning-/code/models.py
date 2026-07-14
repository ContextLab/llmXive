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
    NONE = "none"

class CleaningStrategyType(str, Enum):
    OUTLIER_REMOVAL = "outlier_removal"
    IMPUTATION = "imputation"
    RECATEGORIZATION = "recategorization"
    COMBINED = "combined"

class Dataset(BaseModel):
    """Represents a loaded dataset with metadata."""
    name: str
    source: str
    path: str
    checksum: str
    rows: int
    columns: int
    missing_rates: Dict[str, float]
    loaded_at: datetime = Field(default_factory=datetime.now)

class CleaningStrategy(BaseModel):
    """Defines a cleaning strategy to be applied."""
    strategy_type: CleaningStrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str

class AnalysisResult(BaseModel):
    """Results from statistical analysis on a dataset."""
    dataset_name: str
    strategy: Optional[str] = None
    t_test: Dict[str, Any] = Field(default_factory=dict)
    regression: Optional[Dict[str, Any]] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[List[float]] = None
    p_value: float
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

class ComparisonReport(BaseModel):
    """
    Comprehensive comparison report between baseline and cleaned metrics.
    Includes absolute and relative differences, and sensitivity analysis.
    """
    created_at: str
    baseline_metrics: Optional[Dict[str, Any]]
    cleaned_metrics: Optional[Dict[str, Any]]
    absolute_diffs: List[float]
    relative_diffs: List[float]
    sensitivity_analysis: Optional[Dict[str, Any]]
    comparisons: List[Dict[str, Any]]
    inconsistency_rate: float
    total_datasets_analyzed: int = 0

    @field_validator('absolute_diffs', 'relative_diffs')
    @classmethod
    def validate_diffs(cls, v):
        if not isinstance(v, list):
            raise ValueError('Diffs must be a list')
        return v