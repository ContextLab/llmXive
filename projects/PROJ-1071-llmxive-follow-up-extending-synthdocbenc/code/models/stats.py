"""
Data models for statistical analysis results.
Matches the schema defined in contracts/stats_schema.yaml
"""
from typing import Any, Dict, List, Optional
from .base import BaseModel

class StatisticalResult(BaseModel):
    """
    Results of the statistical correlation analysis.
    """
    def __init__(
        self,
        model_id: str,
        baseline_accuracy: float,
        retrieval_accuracy: float,
        recovery_delta: float,
        context_window_size: int,
        correlation_coefficient: float,
        p_value: float,
        classification: str,  # 'inverse', 'no significant inverse relationship'
        easy_questions_degraded: bool
    ):
        self.model_id = model_id
        self.baseline_accuracy = baseline_accuracy
        self.retrieval_accuracy = retrieval_accuracy
        self.recovery_delta = recovery_delta
        self.context_window_size = context_window_size
        self.correlation_coefficient = correlation_coefficient
        self.p_value = p_value
        self.classification = classification
        self.easy_questions_degraded = easy_questions_degraded

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatisticalResult':
        return super().from_dict(data)
