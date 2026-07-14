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
    dataset_id: str
    name: str
    source_url: str
    checksum: str
    row_count: int
    column_count: int
    missing_rate: float
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class CleaningStrategy(BaseModel):
    strategy_id: str
    strategy_type: CleaningStrategyType
    parameters: Dict[str, Any]
    description: str

class AnalysisResult(BaseModel):
    dataset_id: str
    test_name: str
    p_value: float
    confidence_interval: List[float]
    effect_size: float
    effect_size_type: str
    significant: bool
    strategy_applied: Optional[str] = None

class ComparisonReport(BaseModel):
    baseline_metrics: Dict[str, Any]
    cleaned_metrics: Dict[str, Any]
    absolute_diff: List[Dict[str, Any]]
    relative_diff: List[Dict[str, Any]]
    sensitivity_analysis: Optional[Dict[str, Any]]
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())