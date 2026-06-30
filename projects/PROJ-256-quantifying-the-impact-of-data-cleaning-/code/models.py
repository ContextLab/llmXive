"""
Data models and entities for the Quantifying the Impact of Data Cleaning pipeline.

Defines Pydantic schemas for Dataset, CleaningStrategy, AnalysisResult, and ComparisonReport.
These models ensure type safety and validation across the research pipeline.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ImputationMethod(str, Enum):
    """Enumeration of supported imputation methods."""
    MEAN = "mean"
    MEDIAN = "median"
    KNN = "knn"


class CleaningStrategyType(str, Enum):
    """Enumeration of cleaning strategy types."""
    OUTLIER_REMOVAL = "outlier_removal"
    IMPUTATION = "imputation"
    CATEGORICAL_RECODING = "categorical_recoding"


class Dataset(BaseModel):
    """
    Represents a raw or processed dataset used in the analysis.
    
    Attributes:
        id: Unique identifier for the dataset instance.
        name: Human-readable name of the dataset.
        source_url: URL where the dataset was downloaded from.
        file_path: Local path to the dataset file (CSV).
        checksum: SHA256 checksum of the file for integrity validation.
        row_count: Number of rows in the dataset.
        column_count: Number of columns in the dataset.
        missing_rate: Proportion of missing values (0.0 to 1.0).
        created_at: Timestamp of dataset creation/loading.
    """
    id: str
    name: str
    source_url: str
    file_path: str
    checksum: str
    row_count: int
    column_count: int
    missing_rate: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator('missing_rate')
    @classmethod
    def validate_missing_rate(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("missing_rate must be between 0.0 and 1.0")
        return v


class CleaningStrategy(BaseModel):
    """
    Represents a specific data cleaning operation applied to a dataset.
    
    Attributes:
        id: Unique identifier for the strategy instance.
        strategy_type: Type of cleaning (e.g., outlier removal, imputation).
        method: Specific method used (e.g., mean, median, IQR).
        parameters: Dictionary of hyperparameters used (e.g., k=1.5 for IQR).
        rows_removed: Number of rows removed during cleaning.
        rows_imputed: Number of rows/cells imputed.
        applied_at: Timestamp of application.
    """
    id: str
    strategy_type: CleaningStrategyType
    method: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rows_removed: int = 0
    rows_imputed: int = 0
    applied_at: datetime = Field(default_factory=datetime.now)


class AnalysisResult(BaseModel):
    """
    Represents the statistical results from analyzing a dataset (baseline or cleaned).
    
    Attributes:
        dataset_id: Reference to the dataset analyzed.
        strategy_id: Reference to the cleaning strategy applied (None for baseline).
        test_type: Type of statistical test performed (e.g., t-test, linear_regression).
        p_value: Resulting p-value from the test.
        confidence_interval: Tuple of (lower, upper) bounds for the 95% CI.
        effect_size: Calculated effect size (e.g., Cohen's d, R-squared).
        significant: Boolean indicating if p_value < 0.05.
        test_statistic: The raw test statistic value (t-value, F-value, etc.).
        degrees_of_freedom: Degrees of freedom for the test.
        notes: Any warnings or notes about the test execution.
    """
    dataset_id: str
    strategy_id: Optional[str] = None
    test_type: str
    p_value: float = Field(ge=0.0, le=1.0)
    confidence_interval: tuple[float, float]
    effect_size: float
    significant: bool
    test_statistic: float
    degrees_of_freedom: Optional[float] = None
    notes: Optional[str] = None

    @field_validator('p_value')
    @classmethod
    def validate_p_value(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("p_value must be between 0.0 and 1.0")
        return v

    @field_validator('confidence_interval')
    @classmethod
    def validate_ci(cls, v: tuple) -> tuple:
        if len(v) != 2:
            raise ValueError("confidence_interval must be a tuple of 2 floats")
        if not (isinstance(v[0], (int, float)) and isinstance(v[1], (int, float))):
            raise ValueError("CI bounds must be numeric")
        return v


class ComparisonReport(BaseModel):
    """
    Aggregated report comparing baseline metrics against cleaned metrics.
    
    Attributes:
        report_id: Unique identifier for the report.
        dataset_id: The dataset this report pertains to.
        baseline_result: The original AnalysisResult before cleaning.
        cleaned_results: List of AnalysisResults after applying different cleaning strategies.
        absolute_diff_p: Absolute difference in p-values (|p_cleaned - p_baseline|).
        relative_diff_p: Relative difference in p-values.
        ci_width_change: Change in confidence interval width.
        effect_size_delta: Difference in effect size.
        inconsistency_rate: Proportion of tests where significance status changed.
        sensitivity_analysis: Dictionary of sensitivity metrics (e.g., by bin).
        generated_at: Timestamp of report generation.
    """
    report_id: str
    dataset_id: str
    baseline_result: AnalysisResult
    cleaned_results: List[AnalysisResult]
    absolute_diff_p: float
    relative_diff_p: float
    ci_width_change: float
    effect_size_delta: float
    inconsistency_rate: float = 0.0
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('absolute_diff_p', 'relative_diff_p', 'ci_width_change', 'effect_size_delta', 'inconsistency_rate')
    @classmethod
    def validate_numeric_fields(cls, v: float) -> float:
        if not isinstance(v, (int, float)):
            raise ValueError("Comparison metrics must be numeric")
        return v