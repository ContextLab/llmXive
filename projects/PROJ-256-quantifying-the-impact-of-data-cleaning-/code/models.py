from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ImputationMethod(str):
    """Enum‑like holder for imputation method names."""
    MEAN = "mean"
    MEDIAN = "median"
    KNN = "knn"


class CleaningStrategyType(str):
    """Enum‑like holder for cleaning strategy identifiers."""
    IQR_OUTLIER = "iqr_outlier_removal"
    MEAN_IMPUTATION = "mean_imputation"
    MEDIAN_IMPUTATION = "median_imputation"
    KNN_IMPUTATION = "knn_imputation"
    CATEGORICAL_RECODING = "categorical_recoding"


class Dataset(BaseModel):
    name: str
    description: Optional[str] = None
    n_rows: int
    n_columns: int
    path: str


class CleaningStrategy(BaseModel):
    name: CleaningStrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    dataset_name: str
    analysis: Dict[str, Any]  # raw output from ``analysis.run_baseline_analysis``


class ComparisonReport(BaseModel):
    """
    Consolidated report comparing baseline and cleaned analysis results.
    """
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    baseline_metrics: Dict[str, Any] = Field(default_factory=dict)
    cleaned_metrics: Dict[str, Any] = Field(default_factory=dict)
    absolute_diff: Dict[str, Any] = Field(default_factory=dict)
    relative_diff: Dict[str, Any] = Field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)
