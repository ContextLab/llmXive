"""
PredictionResult model generated from contracts/prediction.schema.yaml.
This module ensures schema drift prevention by deriving the data structure
directly from the contract definition using Pydantic.
"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
import time
from src.models.code_snippet import CodeSnippet
from pydantic import BaseModel, Field


class PredictionResultSchema(BaseModel):
    """Pydantic schema corresponding to contracts/prediction.schema.yaml."""
    snippet_id: str = Field(..., description="Unique identifier for the code snippet")
    predicted_label: str = Field(..., description="Label predicted by the LLM or static analyzer")
    predicted_category: str = Field(..., description="Category of the vulnerability (e.g., SQLi, Buffer Overflow, none)")
    is_correct: bool = Field(..., description="Boolean flag indicating if prediction matches ground truth")
    inference_time_ms: float = Field(..., description="Time taken for inference in milliseconds")


@dataclass
class PredictionResult:
    """
    Data class representing a prediction result.
    Generated from the schema to ensure consistency with the contract.
    """
    snippet_id: str
    predicted_label: str
    predicted_category: str
    is_correct: bool
    inference_time_ms: float

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary."""
        return {
            "snippet_id": self.snippet_id,
            "predicted_label": self.predicted_label,
            "predicted_category": self.predicted_category,
            "is_correct": self.is_correct,
            "inference_time_ms": self.inference_time_ms
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PredictionResult":
        """Create a PredictionResult instance from a dictionary."""
        # Validate against Pydantic schema first to ensure contract compliance
        schema = PredictionResultSchema(**data)
        return cls(
            snippet_id=schema.snippet_id,
            predicted_label=schema.predicted_label,
            predicted_category=schema.predicted_category,
            is_correct=schema.is_correct,
            inference_time_ms=schema.inference_time_ms
        )


def create_prediction_result(
    snippet_id: Optional[str] = None,
    predicted_label: str = "unknown",
    predicted_category: str = "uncertain",
    is_correct: bool = False,
    inference_time_ms: float = 0.0
) -> PredictionResult:
    """
    Factory function to create a PredictionResult instance.
    If snippet_id is not provided, a UUID is generated.
    """
    if snippet_id is None:
        snippet_id = str(uuid.uuid4())
    return PredictionResult(
        snippet_id=snippet_id,
        predicted_label=predicted_label,
        predicted_category=predicted_category,
        is_correct=is_correct,
        inference_time_ms=inference_time_ms
    )


def prediction_result_to_dict(result: PredictionResult) -> dict:
    """Helper to serialize a PredictionResult to a dictionary."""
    return result.to_dict()


def dict_to_prediction_result(data: dict) -> PredictionResult:
    """Helper to deserialize a dictionary to a PredictionResult."""
    return PredictionResult.from_dict(data)
