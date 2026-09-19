"""
Inference result entity definition.

This module defines the InferenceResult dataclass used to store
the outcome of a single inference run, including retrieval accuracy
and resource usage metrics.
"""
from dataclasses import dataclass
from typing import Optional
import time
import json
from pathlib import Path


@dataclass
class InferenceResult:
    """
    Represents the result of a single inference execution.

    Attributes:
        sample_id: Unique identifier for the input sample.
        retrieved_value: The value retrieved by the model (e.g., the "needle").
        is_correct: Boolean indicating if the retrieved value matches the ground truth.
        inference_time_ms: Time taken for the inference step in milliseconds.
        peak_memory_mb: Peak memory usage in megabytes during this inference.
    """
    sample_id: str
    retrieved_value: Optional[str]
    is_correct: bool
    inference_time_ms: float
    peak_memory_mb: float

    def to_dict(self) -> dict:
        """Convert the result to a dictionary for serialization."""
        return {
            "sample_id": self.sample_id,
            "retrieved_value": self.retrieved_value,
            "is_correct": self.is_correct,
            "inference_time_ms": self.inference_time_ms,
            "peak_memory_mb": self.peak_memory_mb
        }

    def to_json(self) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "InferenceResult":
        """Create an InferenceResult instance from a dictionary."""
        return cls(
            sample_id=data["sample_id"],
            retrieved_value=data.get("retrieved_value"),
            is_correct=data["is_correct"],
            inference_time_ms=data["inference_time_ms"],
            peak_memory_mb=data["peak_memory_mb"]
        )

    @classmethod
    def create_mock(cls, sample_id: str = "mock_001") -> "InferenceResult":
        """
        Create a mock InferenceResult for testing purposes.
        This is used for verification that the dataclass can be instantiated
        and imported correctly, as per T009 requirements.
        """
        return cls(
            sample_id=sample_id,
            retrieved_value="mock_needle_value",
            is_correct=True,
            inference_time_ms=150.5,
            peak_memory_mb=4096.0
        )

# Verification block for standalone execution
if __name__ == "__main__":
    # Test instantiation with mock data
    result = InferenceResult.create_mock("test_sample_123")
    
    # Verify attributes
    assert result.sample_id == "test_sample_123"
    assert result.retrieved_value == "mock_needle_value"
    assert result.is_correct is True
    assert isinstance(result.inference_time_ms, float)
    assert isinstance(result.peak_memory_mb, float)
    
    # Test serialization
    json_str = result.to_json()
    assert "test_sample_123" in json_str
    
    # Test deserialization
    loaded = InferenceResult.from_dict(result.to_dict())
    assert loaded.sample_id == result.sample_id
    assert loaded.is_correct == result.is_correct
    
    print(f"Verification successful: {result}")
    print(f"JSON Output: {json_str}")