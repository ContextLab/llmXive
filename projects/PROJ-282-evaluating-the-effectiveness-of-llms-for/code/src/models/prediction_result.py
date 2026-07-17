from dataclasses import dataclass, field
from typing import Optional
import uuid
import time
from src.models.code_snippet import CodeSnippet


@dataclass
class PredictionResult:
    """
    Dataclass representing the result of an LLM or static analyzer prediction
    on a code snippet.

    Attributes:
        snippet_id: Unique identifier for the code snippet being analyzed.
        predicted_label: The label predicted by the model (e.g., 'vulnerable', 'safe').
        predicted_category: The specific vulnerability category predicted (e.g., 'SQLi', 'XSS').
        is_correct: Boolean indicating if the prediction matches the ground truth.
        inference_time_ms: Time taken to perform the inference in milliseconds.
        model_id: (Optional) Identifier of the model used for prediction.
        confidence_score: (Optional) Confidence score of the prediction (0.0 to 1.0).
        raw_output: (Optional) The raw text output from the model before parsing.
    """
    snippet_id: str
    predicted_label: str
    predicted_category: Optional[str] = None
    is_correct: Optional[bool] = None
    inference_time_ms: float = 0.0
    model_id: Optional[str] = None
    confidence_score: Optional[float] = None
    raw_output: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate the prediction result after initialization."""
        if not self.snippet_id:
            raise ValueError("snippet_id cannot be empty")
        if not self.predicted_label:
            raise ValueError("predicted_label cannot be empty")
        
        # Validate confidence score range if provided
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                raise ValueError("confidence_score must be between 0.0 and 1.0")
        
        # Validate inference time
        if self.inference_time_ms < 0:
            raise ValueError("inference_time_ms cannot be negative")


def create_prediction_result(
    snippet: CodeSnippet,
    predicted_label: str,
    predicted_category: Optional[str] = None,
    is_correct: Optional[bool] = None,
    inference_time_ms: float = 0.0,
    model_id: Optional[str] = None,
    confidence_score: Optional[float] = None,
    raw_output: Optional[str] = None
) -> PredictionResult:
    """
    Factory function to create a PredictionResult from a CodeSnippet.
    
    Args:
        snippet: The CodeSnippet object containing ground truth information.
        predicted_label: The label predicted by the model.
        predicted_category: The specific vulnerability category predicted.
        is_correct: Whether the prediction matches the ground truth.
        inference_time_ms: Time taken for inference in milliseconds.
        model_id: Identifier of the model used.
        confidence_score: Confidence score of the prediction.
        raw_output: Raw model output text.
        
    Returns:
        A PredictionResult instance.
    """
    # Determine correctness if ground truth is available
    if is_correct is None and snippet.ground_truth_label is not None:
        is_correct = (predicted_label.lower() == snippet.ground_truth_label.lower())
    
    # Infer category if not provided but ground truth has one
    if predicted_category is None and snippet.ground_truth_category is not None:
        # For now, we might not infer category from prediction unless the model
        # specifically returns it. Keeping as None if not provided.
        pass
    
    return PredictionResult(
        snippet_id=snippet.id,
        predicted_label=predicted_label,
        predicted_category=predicted_category,
        is_correct=is_correct,
        inference_time_ms=inference_time_ms,
        model_id=model_id,
        confidence_score=confidence_score,
        raw_output=raw_output
    )


def prediction_result_to_dict(result: PredictionResult) -> dict:
    """
    Convert a PredictionResult to a dictionary for serialization.
    
    Args:
        result: The PredictionResult instance.
        
    Returns:
        Dictionary representation of the prediction result.
    """
    return {
        'id': result.id,
        'snippet_id': result.snippet_id,
        'predicted_label': result.predicted_label,
        'predicted_category': result.predicted_category,
        'is_correct': result.is_correct,
        'inference_time_ms': result.inference_time_ms,
        'model_id': result.model_id,
        'confidence_score': result.confidence_score,
        'raw_output': result.raw_output,
        'created_at': result.created_at
    }


def dict_to_prediction_result(data: dict) -> PredictionResult:
    """
    Create a PredictionResult from a dictionary.
    
    Args:
        data: Dictionary containing prediction result fields.
        
    Returns:
        A PredictionResult instance.
    """
    return PredictionResult(
        snippet_id=data['snippet_id'],
        predicted_label=data['predicted_label'],
        predicted_category=data.get('predicted_category'),
        is_correct=data.get('is_correct'),
        inference_time_ms=data.get('inference_time_ms', 0.0),
        model_id=data.get('model_id'),
        confidence_score=data.get('confidence_score'),
        raw_output=data.get('raw_output'),
        id=data.get('id', str(uuid.uuid4())),
        created_at=data.get('created_at', time.time())
    )
