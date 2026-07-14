"""
Data models and entities for the Quantifying Impact of Data Cleaning project.
"""
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
    missing_rate: float
    checksum: str

class CleaningStrategy(BaseModel):
    type: CleaningStrategyType
    parameters: Dict[str, Any]
    description: str

class AnalysisResult(BaseModel):
    dataset_id: str
    strategy: Optional[str] = None
    t_tests: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    regressions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    effect_sizes: Dict[str, float] = Field(default_factory=dict)
    execution_time: float

class ComparisonReport(BaseModel):
    id: str
    created_at: str
    baseline_metrics: Dict[str, Any]
    cleaned_metrics: Dict[str, Any]
    absolute_diff: float
    relative_diff: float
    sensitivity_analysis: Dict[str, Any]
    dataset_comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)

def main():
    """Main entry point for model validation (if needed)."""
    pass
