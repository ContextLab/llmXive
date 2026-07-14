from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

# ----------------------------------------------------------------------
# Enumerations
# ----------------------------------------------------------------------

class CleaningStrategyType(str, Enum):
    """
    Enum describing the type of cleaning strategy applied to a dataset.
    Subclassing ``str`` ensures seamless JSON (de)serialization and
    compatibility with Pydantic schema generation.
    """
    IQR_OUTLIER_REMOVAL = "iqr_outlier_removal"
    MEAN_IMPUTATION = "mean_imputation"
    MEDIAN_IMPUTATION = "median_imputation"
    KNN_IMPUTATION = "knn_imputation"
    CATEGORICAL_RECODING = "categorical_recoding"

# ----------------------------------------------------------------------
# Data models
# ----------------------------------------------------------------------

class Dataset(BaseModel):
    """
    Minimal representation of a dataset used in the pipeline.
    """
    name: str
    path: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Allow arbitrary types (e.g., pandas DataFrames) if they ever appear.
    model_config = ConfigDict(arbitrary_types_allowed=True)

class CleaningStrategy(BaseModel):
    """
    Configuration for a cleaning strategy.
    """
    name: str
    type: CleaningStrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class AnalysisResult(BaseModel):
    """
    Result of a single statistical analysis (e.g., t‑test or regression) on a
    dataset.
    """
    dataset_name: str
    strategy: Optional[CleaningStrategyType] = None
    t_test: Dict[str, Any] = Field(default_factory=dict)
    regression: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class ComparisonReport(BaseModel):
    """
    Aggregated comparison between baseline and cleaned analyses.
    """
    baseline_metrics: List[AnalysisResult] = Field(default_factory=list)
    cleaned_metrics: List[AnalysisResult] = Field(default_factory=list)
    absolute_diff: Dict[str, Any] = Field(default_factory=dict)
    relative_diff: Dict[str, Any] = Field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

# ----------------------------------------------------------------------
# Helper: make all BaseModel subclasses tolerant of unknown field types
# ----------------------------------------------------------------------

# This loop ensures that any BaseModel defined elsewhere in this module (or
# imported later) automatically receives ``arbitrary_types_allowed=True``.
# It is a defensive measure to avoid schema generation errors for custom
# types such as ``CleaningStrategyType``.
import inspect
for _name, _obj in list(globals().items()):
    if inspect.isclass(_obj) and issubclass(_obj, BaseModel):
        if not hasattr(_obj, "model_config"):
            _obj.model_config = ConfigDict(arbitrary_types_allowed=True)
