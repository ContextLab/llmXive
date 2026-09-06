"""
Pydantic models for type-safe data validation in the llmXive pipeline.

These models correspond to the JSON schemas defined in:
- code/contracts/dataset.schema.yaml (TimeSeriesRecord)
- code/contracts/output.schema.yaml (AnalysisResult)
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ValidationError


class TimeSeriesRecord(BaseModel):
    """
    Model representing a single record in the time-series dataset.
    Matches code/contracts/dataset.schema.yaml.

    Fields:
        date: Date string in YYYY-MM-DD format.
        value: Numeric value associated with the date.
        source: String identifier for the data source.
    """
    date: str = Field(
        ...,
        description="Date string in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    value: float = Field(..., description="Numeric value")
    source: str = Field(..., description="Data source identifier")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure the date string is a valid date in YYYY-MM-DD format."""
        try:
            # Validate that it's an actual date, not just a regex match
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD.")


class AnalysisResult(BaseModel):
    """
    Model representing a single analysis result entry.
    Matches code/contracts/output.schema.yaml.

    Fields:
        metric: Name of the metric being analyzed.
        coefficient: The calculated coefficient value.
        p_value: The p-value from the statistical test.
        lag: The lag value used in the analysis.
        significance_flag: Boolean indicating statistical significance.
        stationarity_status: String describing the stationarity status.
    """
    metric: str = Field(..., description="Metric name")
    coefficient: float = Field(..., description="Coefficient value")
    p_value: float = Field(..., description="P-value")
    lag: int = Field(..., description="Lag value")
    significance_flag: bool = Field(..., description="Significance flag")
    stationarity_status: str = Field(..., description="Stationarity status")

    @field_validator('p_value')
    @classmethod
    def validate_p_value_range(cls, v: float) -> float:
        """Ensure p-value is between 0 and 1."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"p_value must be between 0 and 1, got {v}")
        return v

    @field_validator('coefficient')
    @classmethod
    def validate_coefficient(cls, v: float) -> float:
        """Ensure coefficient is a finite number."""
        if not (v == v):  # NaN check
            raise ValueError("Coefficient cannot be NaN")
        if abs(v) == float('inf'):
            raise ValueError("Coefficient cannot be infinite")
        return v


# Optional: Helper function to validate a dictionary against TimeSeriesRecord
def validate_time_series_record(data: dict) -> TimeSeriesRecord:
    """
    Validates a dictionary against the TimeSeriesRecord model.

    Args:
        data: Dictionary containing 'date', 'value', and 'source' keys.

    Returns:
        A validated TimeSeriesRecord instance.

    Raises:
        ValidationError: If the data does not conform to the model.
    """
    return TimeSeriesRecord(**data)


# Optional: Helper function to validate a dictionary against AnalysisResult
def validate_analysis_result(data: dict) -> AnalysisResult:
    """
    Validates a dictionary against the AnalysisResult model.

    Args:
        data: Dictionary containing required keys for AnalysisResult.

    Returns:
        A validated AnalysisResult instance.

    Raises:
        ValidationError: If the data does not conform to the model.
    """
    return AnalysisResult(**data)