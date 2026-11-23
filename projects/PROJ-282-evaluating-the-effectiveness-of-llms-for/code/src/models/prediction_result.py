"""
Generated model for PredictionResult based on contracts/prediction.schema.yaml.
DO NOT EDIT MANUALLY. Regenerate from contract if schema changes.
"""
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import time


class PredictionResultSchema(BaseModel):
    """Schema definition for PredictionResult."""
    snippet_id: str = Field(..., description="Unique identifier for the code snippet")
    predicted_label: str = Field(..., description="Predicted vulnerability label (e.g., 'SQLi', 'Buffer Overflow', 'none')")
    predicted_category: str = Field(..., description="Predicted category of the vulnerability")
    is_correct: bool = Field(..., description="Whether the prediction matches the ground truth")
    inference_time_ms: float = Field(..., description="Time taken for inference in milliseconds")


class PredictionResult(BaseModel):
    """
    Pydantic model representing a single prediction result.
    Generated from contracts/prediction.schema.yaml.
    """
    snippet_id: str = Field(..., description="Unique identifier for the code snippet")
    predicted_label: str = Field(..., description="Predicted vulnerability label (e.g., 'SQLi', 'Buffer Overflow', 'none')")
    predicted_category: str = Field(..., description="Predicted category of the vulnerability")
    is_correct: bool = Field(..., description="Whether the prediction matches the ground truth")
    inference_time_ms: float = Field(..., description="Time taken for inference in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "snippet_id": "550e8400-e29b-41d4-a716-446655440000",
                "predicted_label": "SQLi",
                "predicted_category": "SQL Injection",
                "is_correct": True,
                "inference_time_ms": 125.5
            }
        }


def create_prediction_result(
    snippet_id: str,
    predicted_label: str,
    predicted_category: str,
    is_correct: bool,
    inference_time_ms: float
) -> PredictionResult:
    """
    Factory function to create a PredictionResult instance.
    
    Args:
        snippet_id: Unique identifier for the code snippet
        predicted_label: Predicted vulnerability label
        predicted_category: Predicted category of the vulnerability
        is_correct: Whether the prediction matches ground truth
        inference_time_ms: Inference time in milliseconds
        
    Returns:
        PredictionResult instance
    """
    return PredictionResult(
        snippet_id=snippet_id,
        predicted_label=predicted_label,
        predicted_category=predicted_category,
        is_correct=is_correct,
        inference_time_ms=inference_time_ms
    )


def prediction_result_to_dict(result: PredictionResult) -> dict:
    """
    Convert a PredictionResult instance to a dictionary.
    
    Args:
        result: PredictionResult instance
        
    Returns:
        Dictionary representation of the result
    """
    return result.model_dump()


def dict_to_prediction_result(data: dict) -> PredictionResult:
    """
    Create a PredictionResult instance from a dictionary.
    
    Args:
        data: Dictionary containing prediction result data
        
    Returns:
        PredictionResult instance
    """
    return PredictionResult(**data)
