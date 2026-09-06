"""
Statistical analysis result models matching contracts/stats_schema.yaml.
"""
from typing import Any, Dict, List, Optional
from .base import BaseModel

class StatisticalResult(BaseModel):
    """Statistical analysis results for recovery correlation."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "spearman_r": {
                    "type": "number",
                    "required": True,
                    "description": "Spearman rank correlation coefficient"
                },
                "p_value": {
                    "type": "number",
                    "required": True,
                    "description": "P-value for the correlation test"
                },
                "classification": {
                    "type": "string",
                    "required": True,
                    "description": "Classification: 'inverse' or 'no significant inverse relationship'"
                },
                "recovery_deltas": {
                    "type": "array",
                    "required": True,
                    "description": "List of recovery deltas per model"
                },
                "context_sizes": {
                    "type": "array",
                    "required": True,
                    "description": "List of context window sizes per model"
                },
                "models": {
                    "type": "array",
                    "required": True,
                    "description": "List of model names"
                }
            }
        }

    def __init__(
        self,
        spearman_r: float,
        p_value: float,
        classification: str,
        recovery_deltas: List[float],
        context_sizes: List[int],
        models: List[str]
    ):
        data = {
            "spearman_r": spearman_r,
            "p_value": p_value,
            "classification": classification,
            "recovery_deltas": recovery_deltas,
            "context_sizes": context_sizes,
            "models": models
        }
        self._data = self.validate(data)
        self.spearman_r = spearman_r
        self.p_value = p_value
        self.classification = classification
        self.recovery_deltas = recovery_deltas
        self.context_sizes = context_sizes
        self.models = models

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spearman_r": self.spearman_r,
            "p_value": self.p_value,
            "classification": self.classification,
            "recovery_deltas": self.recovery_deltas,
            "context_sizes": self.context_sizes,
            "models": self.models
        }
