from dataclasses import dataclass, field
from typing import Optional
import uuid
import time
from src.models.code_snippet import CodeSnippet
from pydantic import BaseModel, Field

# Schema definition matches contracts/prediction.schema.yaml
class PredictionResultSchema(BaseModel):
    snippet_id: str
    predicted_label: str
    predicted_category: str
    is_correct: bool
    inference_time_ms: float

    class Config:
        json_schema_extra = {
            "type": "object",
            "properties": {
                "snippet_id": {"type": "string"},
                "predicted_label": {"type": "string"},
                "predicted_category": {"type": "string"},
                "is_correct": {"type": "boolean"},
                "inference_time_ms": {"type": "number"}
            },
            "required": ["snippet_id", "predicted_label", "predicted_category", "is_correct", "inference_time_ms"]
        }

@dataclass
class PredictionResult:
    snippet_id: str
    predicted_label: str
    predicted_category: str
    is_correct: bool
    inference_time_ms: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "snippet_id": self.snippet_id,
            "predicted_label": self.predicted_label,
            "predicted_category": self.predicted_category,
            "is_correct": self.is_correct,
            "inference_time_ms": self.inference_time_ms,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            snippet_id=data.get("snippet_id", str(uuid.uuid4())),
            predicted_label=data.get("predicted_label", "unknown"),
            predicted_category=data.get("predicted_category", "unknown"),
            is_correct=data.get("is_correct", False),
            inference_time_ms=data.get("inference_time_ms", 0.0),
            timestamp=data.get("timestamp", time.time())
        )

def create_prediction_result(
    snippet_id: str,
    predicted_label: str,
    predicted_category: str,
    is_correct: bool,
    inference_time_ms: float
) -> PredictionResult:
    """Factory function to create a PredictionResult."""
    return PredictionResult(
        snippet_id=snippet_id,
        predicted_label=predicted_label,
        predicted_category=predicted_category,
        is_correct=is_correct,
        inference_time_ms=inference_time_ms
    )

def prediction_result_to_dict(result: PredictionResult) -> dict:
    return result.to_dict()

def dict_to_prediction_result(data: dict) -> PredictionResult:
    return PredictionResult.from_dict(data)
