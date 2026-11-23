from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class StatisticalTestResult(BaseModel):
    """Schema for a single statistical test result (e.g., K-S test, Change Point)."""
    test_name: str = Field(..., description="Name of the statistical test")
    statistic: float = Field(..., description="Test statistic value")
    p_value: Optional[float] = Field(None, description="P-value (if applicable)")
    threshold: Optional[float] = Field(None, description="Identified threshold (for change point)")
    significance_level: float = Field(default=0.05, description="Significance level used")
    conclusion: str = Field(..., description="Textual conclusion")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional test details")


class AnalysisResultSchema(BaseModel):
    """Pydantic schema for a single analysis result record."""
    result_id: str = Field(..., description="Unique identifier")
    analysis_type: str = Field(..., description="Type of analysis (e.g., 'sensitivity', 'threshold')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")
    parameters: Dict[str, Any] = Field(..., description="Parameters used in analysis")
    results: List[StatisticalTestResult] = Field(..., description="List of test results")
    summary: str = Field(..., description="Executive summary of the analysis")


class AnalysisSchema(BaseModel):
    """Pydantic schema for a complete analysis report."""
    report_id: str = Field(..., description="Unique report identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    comparisons: List[AnalysisResultSchema] = Field(..., description="List of analysis results")
    total_comparisons: int = Field(..., description="Total number of comparisons")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Report metadata")

    @field_validator('total_comparisons')
    @classmethod
    def validate_total_comparisons(cls, v, info):
        comparisons = info.data.get('comparisons', [])
        if v != len(comparisons):
            raise ValueError(f"total_comparisons ({v}) must match number of comparisons ({len(comparisons)})")
        return v


class AnalysisValidator:
    """
    Validator class to enforce AnalysisSchema constraints and validate JSON records.
    """
    @staticmethod
    def validate_from_json(json_str: str) -> AnalysisSchema:
        """
        Validates a JSON string against AnalysisSchema.
        Raises pydantic.ValidationError on mismatch.
        """
        data = json.loads(json_str)
        return AnalysisSchema(**data)

    @staticmethod
    def validate_from_dict(data: Dict[str, Any]) -> AnalysisSchema:
        """
        Validates a dictionary against AnalysisSchema.
        """
        return AnalysisSchema(**data)

    @staticmethod
    def validate_result_from_json(json_str: str) -> AnalysisResultSchema:
        """
        Validates a JSON string against AnalysisResultSchema.
        """
        data = json.loads(json_str)
        return AnalysisResultSchema(**data)

    @staticmethod
    def validate_result_from_dict(data: Dict[str, Any]) -> AnalysisResultSchema:
        """
        Validates a dictionary against AnalysisResultSchema.
        """
        return AnalysisResultSchema(**data)
