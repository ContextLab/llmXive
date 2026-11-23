from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import inspect

class CleaningStrategyType(str, Enum):
    IQR_OUTLIER_REMOVAL = "iqr_outlier_removal"
    MEAN_IMPUTATION = "mean_imputation"
    MEDIAN_IMPUTATION = "median_imputation"
    KNN_IMPUTATION = "knn_imputation"
    CATEGORICAL_RECODING = "categorical_recoding"

class Dataset(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str
    path: str
    size: int
    outcome_column: str
    missingness_rate: float
    metadata: Optional[Dict[str, Any]] = None

class CleaningStrategy(BaseModel):
    type: CleaningStrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AnalysisResult(BaseModel):
    dataset_id: str
    strategy: Optional[CleaningStrategyType] = None
    t_test: Dict[str, Any]
    linear_regression: Dict[str, Any]
    assumptions_met: bool
    cohens_d: Optional[float] = None

class ComparisonReport(BaseModel):
    baseline: AnalysisResult
    cleaned: AnalysisResult
    absolute_diff: Dict[str, float]
    relative_diff: Dict[str, float]
    inconsistency_rate: float