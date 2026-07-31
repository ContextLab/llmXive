from pydantic import BaseModel, Field
from typing import Optional

# Schema definition matches contracts/analysis_metric.schema.yaml
class AnalysisMetricSchema(BaseModel):
    metric_name: str
    feature_name: str
    value: float
    p_value: float
    adjusted_p_value: float
    method: str

    class Config:
        json_schema_extra = {
            "type": "object",
            "properties": {
                "metric_name": {"type": "string"},
                "feature_name": {"type": "string"},
                "value": {"type": "number"},
                "p_value": {"type": "number"},
                "adjusted_p_value": {"type": "number"},
                "method": {"type": "string"}
            },
            "required": ["metric_name", "feature_name", "value", "p_value", "adjusted_p_value", "method"]
        }

class AnalysisMetric(BaseModel):
    metric_name: str
    feature_name: str
    value: float
    p_value: float
    adjusted_p_value: float
    method: str

    def to_dict(self):
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

def create_analysis_metric(
    metric_name: str,
    feature_name: str,
    value: float,
    p_value: float,
    adjusted_p_value: float,
    method: str
) -> AnalysisMetric:
    """Factory function to create an AnalysisMetric."""
    return AnalysisMetric(
        metric_name=metric_name,
        feature_name=feature_name,
        value=value,
        p_value=p_value,
        adjusted_p_value=adjusted_p_value,
        method=method
    )
