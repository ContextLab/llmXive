"""
PredictionResult Model
Generated from contracts/prediction.schema.yaml (T009a)
Constraint: Do NOT manually implement fields; ensure schema drift is prevented.
"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
import time
from src.models.code_snippet import CodeSnippet


@dataclass
class PredictionResult:
    """
    Represents the result of an LLM inference on a code snippet.
    Generated from prediction.schema.yaml contract.
    """
    snippet_id: str
    predicted_label: str
    predicted_category: str
    is_correct: bool
    inference_time_ms: float
    
    # Optional metadata for tracking
    model_name: Optional[str] = field(default=None, repr=False)
    prompt_id: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        """
        Validation logic to ensure data integrity post-initialization.
        """
        if not self.snippet_id:
            raise ValueError("snippet_id cannot be empty")
        if not self.predicted_label:
            raise ValueError("predicted_label cannot be empty")
        if not self.predicted_category:
            raise ValueError("predicted_category cannot be empty")
        if self.inference_time_ms < 0:
            raise ValueError("inference_time_ms cannot be negative")


def create_prediction_result(
    snippet_id: Optional[str] = None,
    predicted_label: str = "uncertain",
    predicted_category: str = "uncertain",
    is_correct: Optional[bool] = None,
    inference_time_ms: float = 0.0,
    model_name: Optional[str] = None,
    code_snippet: Optional[CodeSnippet] = None
) -> PredictionResult:
    """
    Factory function to create a PredictionResult instance.
    If snippet_id is not provided, generates a new UUID.
    If code_snippet is provided, attempts to determine is_correct if ground truth exists.
    """
    if snippet_id is None:
        snippet_id = str(uuid.uuid4())
    
    # Determine correctness if ground truth is available
    if is_correct is None and code_snippet is not None:
        if code_snippet.ground_truth_label is not None:
            is_correct = (predicted_label.lower() == code_snippet.ground_truth_label.lower())
        else:
            is_correct = False # Default to incorrect if no ground truth to compare against
    
    return PredictionResult(
        snippet_id=snippet_id,
        predicted_label=predicted_label,
        predicted_category=predicted_category,
        is_correct=is_correct if is_correct is not None else False,
        inference_time_ms=inference_time_ms,
        model_name=model_name
    )


def prediction_result_to_dict(result: PredictionResult) -> dict:
    """
    Converts a PredictionResult object to a dictionary.
    Useful for serialization to CSV or JSON.
    """
    return {
        "snippet_id": result.snippet_id,
        "predicted_label": result.predicted_label,
        "predicted_category": result.predicted_category,
        "is_correct": result.is_correct,
        "inference_time_ms": result.inference_time_ms,
        "model_name": result.model_name
    }


def dict_to_prediction_result(data: dict) -> PredictionResult:
    """
    Converts a dictionary to a PredictionResult object.
    Used for deserialization from CSV or JSON.
    """
    return PredictionResult(
        snippet_id=data.get("snippet_id", str(uuid.uuid4())),
        predicted_label=data.get("predicted_label", "uncertain"),
        predicted_category=data.get("predicted_category", "uncertain"),
        is_correct=bool(data.get("is_correct", False)),
        inference_time_ms=float(data.get("inference_time_ms", 0.0)),
        model_name=data.get("model_name")
    )
