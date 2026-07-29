"""
PredictionResult model generated from contracts/prediction.schema.yaml.
This file is auto-generated to prevent schema drift (Constitution IV).
"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
import time
from src.models.code_snippet import CodeSnippet


@dataclass
class PredictionResult:
    """
    Dataclass representing a prediction result for a code snippet.
    Generated from contracts/prediction.schema.yaml.
    """
    snippet_id: str
    model_id: str
    predicted_label: str
    confidence: float
    ground_truth_label: str
    is_correct: bool
    inference_time_ms: Optional[float] = None
    raw_response: Optional[str] = None

    def __post_init__(self):
        # Validate types and constraints
        if not isinstance(self.snippet_id, str) or not self.snippet_id:
            raise ValueError("snippet_id must be a non-empty string")
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be a non-empty string")
        if not isinstance(self.predicted_label, str):
            raise ValueError("predicted_label must be a string")
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be a float between 0.0 and 1.0")
        if not isinstance(self.ground_truth_label, str):
            raise ValueError("ground_truth_label must be a string")
        if not isinstance(self.is_correct, bool):
            raise ValueError("is_correct must be a boolean")
        if self.inference_time_ms is not None and (not isinstance(self.inference_time_ms, (int, float)) or self.inference_time_ms < 0):
            raise ValueError("inference_time_ms must be a non-negative number")

def create_prediction_result(
    snippet_id: str,
    model_id: str,
    predicted_label: str,
    confidence: float,
    ground_truth_label: str,
    inference_time_ms: Optional[float] = None,
    raw_response: Optional[str] = None
) -> PredictionResult:
    """
    Factory function to create a PredictionResult instance.
    Calculates is_correct automatically.
    """
    is_correct = (predicted_label.lower() == ground_truth_label.lower())
    return PredictionResult(
        snippet_id=snippet_id,
        model_id=model_id,
        predicted_label=predicted_label,
        confidence=confidence,
        ground_truth_label=ground_truth_label,
        is_correct=is_correct,
        inference_time_ms=inference_time_ms,
        raw_response=raw_response
    )

def prediction_result_to_dict(result: PredictionResult) -> dict:
    """Convert a PredictionResult instance to a dictionary."""
    return {
        "snippet_id": result.snippet_id,
        "model_id": result.model_id,
        "predicted_label": result.predicted_label,
        "confidence": result.confidence,
        "ground_truth_label": result.ground_truth_label,
        "is_correct": result.is_correct,
        "inference_time_ms": result.inference_time_ms,
        "raw_response": result.raw_response
    }

def dict_to_prediction_result(data: dict) -> PredictionResult:
    """Create a PredictionResult instance from a dictionary."""
    return PredictionResult(
        snippet_id=data["snippet_id"],
        model_id=data["model_id"],
        predicted_label=data["predicted_label"],
        confidence=data["confidence"],
        ground_truth_label=data["ground_truth_label"],
        is_correct=data["is_correct"],
        inference_time_ms=data.get("inference_time_ms"),
        raw_response=data.get("raw_response")
    )
