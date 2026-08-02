"""
Generated model for AnalysisMetric based on contracts/analysis_metric.schema.yaml.
DO NOT EDIT MANUALLY. Regenerate if the schema changes.
"""
from pydantic import BaseModel, Field
from typing import Optional

class AnalysisMetricSchema(BaseModel):
    """Schema definition for AnalysisMetric."""
    metric_name: str = Field(..., description="Name of the metric")
    feature_name: str = Field(..., description="Name of the feature")
    value: float = Field(..., description="Metric value")
    p_value: float = Field(..., description="P-value of the test")
    adjusted_p_value: float = Field(..., description="Adjusted p-value (e.g., Bonferroni)")
    method: str = Field(..., description="Statistical method used")

class AnalysisMetric(BaseModel):
    """
    Data model representing a statistical analysis metric result.
    Matches the schema: contracts/analysis_metric.schema.yaml
    """
    metric_name: str = Field(..., description="Name of the metric (e.g., 'Pearson Correlation', 'McNemar')")
    feature_name: str = Field(..., description="Name of the feature being analyzed")
    value: float = Field(..., description="The calculated value of the metric")
    p_value: float = Field(..., description="The raw p-value from the statistical test")
    adjusted_p_value: float = Field(..., description="The p-value adjusted for multiple comparisons")
    method: str = Field(..., description="The statistical method used (e.g., 'Bonferroni', 'Fisher exact')")

    class Config:
        schema_extra = {
            "example": {
                "metric_name": "Pearson Correlation",
                "feature_name": "ast_depth",
                "value": 0.45,
                "p_value": 0.002,
                "adjusted_p_value": 0.012,
                "method": "Bonferroni"
            }
        }

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
    """
    return AnalysisMetric(
        metric_name=metric_name,
        feature_name=feature_name,
        value=value,
        p_value=p_value,
        adjusted_p_value=adjusted_p_value,
        method=method
    )
