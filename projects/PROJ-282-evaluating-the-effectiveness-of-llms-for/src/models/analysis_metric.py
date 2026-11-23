"""
AnalysisMetric model generated from contracts/analysis_metric.schema.yaml.

This module defines the Pydantic models for analysis metrics, ensuring
schema drift is prevented by deriving fields from the contract definition.
"""
from pydantic import BaseModel, Field
from typing import Optional
import json
from datetime import datetime

class AnalysisMetricSchema(BaseModel):
    """
    Pydantic schema for validation of AnalysisMetric data.
    Generated from contracts/analysis_metric.schema.yaml.
    """
    metric_name: str = Field(..., description="Name of the statistical metric (e.g., correlation, p-value)")
    feature_name: str = Field(..., description="Name of the feature being analyzed")
    value: float = Field(..., description="The calculated value of the metric")
    p_value: float = Field(..., description="Raw p-value from the statistical test")
    adjusted_p_value: float = Field(..., description="P-value adjusted for multiple comparisons (e.g., Bonferroni)")
    method: str = Field(..., description="Statistical method used (e.g., Pearson, Spearman, McNemar)")

class AnalysisMetric(AnalysisMetricSchema):
    """
    Core data model for an analysis metric result.
    Extends the schema with utility methods for serialization and factory creation.
    """
    
    def to_dict(self) -> dict:
        """Convert the metric to a dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Convert the metric to a JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisMetric':
        """Create an AnalysisMetric instance from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'AnalysisMetric':
        """Create an AnalysisMetric instance from a JSON string."""
        return cls.model_validate_json(json_str)

def create_analysis_metric(
    metric_name: str,
    feature_name: str,
    value: float,
    p_value: float,
    adjusted_p_value: float,
    method: str
) -> AnalysisMetric:
    """
    Factory function to create an AnalysisMetric instance.
    
    Args:
        metric_name: Name of the metric.
        feature_name: Name of the feature.
        value: The metric value.
        p_value: Raw p-value.
        adjusted_p_value: Adjusted p-value.
        method: Statistical method used.
        
    Returns:
        A validated AnalysisMetric instance.
    """
    return AnalysisMetric(
        metric_name=metric_name,
        feature_name=feature_name,
        value=value,
        p_value=p_value,
        adjusted_p_value=adjusted_p_value,
        method=method
    )
