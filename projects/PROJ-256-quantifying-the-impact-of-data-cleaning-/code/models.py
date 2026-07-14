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
    name: str
    path: str
    n_rows: int
    n_cols: int
    checksum: str
    missing_rate: Optional[float] = None

class CleaningStrategy(BaseModel):
    type: CleaningStrategyType
    parameters: Dict[str, Any]
    rows_removed: Optional[int] = None
    variance_reduction: Optional[float] = None

class AnalysisResult(BaseModel):
    dataset_name: str
    n_rows: int
    n_cols: int
    t_tests: Dict[str, Dict[str, Any]]
    regressions: Dict[str, Dict[str, Any]]

class ComparisonReport(BaseModel):
    baseline_metrics: List[Dict[str, Any]]
    cleaned_metrics: List[Dict[str, Any]]
    absolute_diff: Dict[str, float]
    relative_diff: Dict[str, float]
    sensitivity_analysis: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.now)

def main():
    """CLI for models."""
    print("Models module loaded.")

if __name__ == "__main__":
    main()