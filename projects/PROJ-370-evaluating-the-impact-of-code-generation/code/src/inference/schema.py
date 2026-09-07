from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json

from code.src.extraction.schema import Severity
from code.src.detection.schema import LLMCodeDetectionResult


class InferenceStatus(str, Enum):
    """Enumeration of possible inference job states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class InferenceRequest:
    """
    Represents a single request to the LLM for bug detection.
    
    Attributes:
        pr_id: Unique identifier for the Pull Request.
        repo_name: Name of the repository (e.g., 'owner/repo').
        diff_text: The raw diff text to be analyzed.
        file_path: Path to the file within the repo.
        line_start: Start line number of the diff hunk.
        line_end: End line number of the diff hunk.
        context_window: Optional surrounding context lines.
        llm_detection_result: Optional pre-computed LLM code detection metadata.
        request_metadata: Additional metadata for tracking.
    """
    pr_id: str
    repo_name: str
    diff_text: str
    file_path: str
    line_start: int
    line_end: int
    context_window: Optional[str] = None
    llm_detection_result: Optional[LLMCodeDetectionResult] = None
    request_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the request to a dictionary for serialization."""
        data = {
            "pr_id": self.pr_id,
            "repo_name": self.repo_name,
            "diff_text": self.diff_text,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "context_window": self.context_window,
            "llm_detection_result": self.llm_detection_result.to_dict() if self.llm_detection_result else None,
            "request_metadata": self.request_metadata,
        }
        return data

    def to_json(self) -> str:
        """Serialize the request to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InferenceRequest":
        """Create an InferenceRequest from a dictionary."""
        llm_det = None
        if data.get("llm_detection_result"):
            llm_det = LLMCodeDetectionResult.from_dict(data["llm_detection_result"])
        
        return cls(
            pr_id=data["pr_id"],
            repo_name=data["repo_name"],
            diff_text=data["diff_text"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            context_window=data.get("context_window"),
            llm_detection_result=llm_det,
            request_metadata=data.get("request_metadata", {}),
        )


@dataclass
class InferenceResponse:
    """
    Represents the response from the LLM inference engine.
    
    Attributes:
        request_id: Unique identifier linking back to the InferenceRequest.
        status: The final status of the inference job.
        detected_bugs: List of detected bug descriptions with location and severity.
        model_id: The ID of the model used for inference.
        latency_seconds: Time taken to generate the response.
        raw_output: The raw text output from the model before parsing.
        error_message: Error details if status is FAILED or TIMEOUT.
        metadata: Additional response metadata.
    """
    request_id: str
    status: InferenceStatus
    detected_bugs: List[Dict[str, Any]] = field(default_factory=list)
    model_id: Optional[str] = None
    latency_seconds: Optional[float] = None
    raw_output: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "detected_bugs": self.detected_bugs,
            "model_id": self.model_id,
            "latency_seconds": self.latency_seconds,
            "raw_output": self.raw_output,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Serialize the response to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InferenceResponse":
        """Create an InferenceResponse from a dictionary."""
        status = InferenceStatus(data.get("status", "failed"))
        return cls(
            request_id=data["request_id"],
            status=status,
            detected_bugs=data.get("detected_bugs", []),
            model_id=data.get("model_id"),
            latency_seconds=data.get("latency_seconds"),
            raw_output=data.get("raw_output"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
        )
