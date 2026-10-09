"""
Schema definitions for the Inference module.

Defines data structures for LLM inference requests and responses,
including status tracking and integration with extraction/detection schemas.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json

# Correct import path for Severity enum from the extraction schema
from src.extraction.schema import Severity
from src.detection.schema import LLMCodeDetectionResult


class InferenceStatus(Enum):
    """Status of an inference request."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class InferenceRequest:
    """
    Request structure for LLM inference.
    
    Attributes:
        pr_id: Unique identifier for the pull request.
        repo: Repository name (e.g., 'owner/repo').
        diff_text: The diff content to be analyzed.
        file_path: Path to the file within the PR.
        line_start: Start line number for the context.
        line_end: End line number for the context.
        llm_detection_result: Optional pre-detection result indicating if code is LLM-generated.
        context_window: Optional maximum token limit for the context.
        metadata: Additional metadata for the request.
    """
    pr_id: str
    repo: str
    diff_text: str
    file_path: str
    line_start: int
    line_end: int
    llm_detection_result: Optional[LLMCodeDetectionResult] = None
    context_window: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the request to a dictionary."""
        return {
            "pr_id": self.pr_id,
            "repo": self.repo,
            "diff_text": self.diff_text,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "llm_detection_result": self.llm_detection_result.to_dict() if self.llm_detection_result else None,
            "context_window": self.context_window,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InferenceRequest':
        """Create an InferenceRequest from a dictionary."""
        llm_det = data.get("llm_detection_result")
        if llm_det and isinstance(llm_det, dict):
            llm_det = LLMCodeDetectionResult.from_dict(llm_det)
        
        return cls(
            pr_id=data["pr_id"],
            repo=data["repo"],
            diff_text=data["diff_text"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            llm_detection_result=llm_det,
            context_window=data.get("context_window"),
            metadata=data.get("metadata", {})
        )


@dataclass
class InferenceResponse:
    """
    Response structure from LLM inference.
    
    Attributes:
        pr_id: Unique identifier for the pull request.
        status: Status of the inference request.
        detected_bugs: List of bugs detected by the LLM.
        error_message: Error message if status is FAILED or ERROR.
        latency_seconds: Time taken for inference in seconds.
        tokens_used: Number of tokens used in the request/response.
        model_id: ID of the model used for inference.
        metadata: Additional metadata for the response.
    """
    pr_id: str
    status: InferenceStatus
    detected_bugs: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    latency_seconds: float = 0.0
    tokens_used: int = 0
    model_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary."""
        return {
            "pr_id": self.pr_id,
            "status": self.status.value,
            "detected_bugs": self.detected_bugs,
            "error_message": self.error_message,
            "latency_seconds": self.latency_seconds,
            "tokens_used": self.tokens_used,
            "model_id": self.model_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InferenceResponse':
        """Create an InferenceResponse from a dictionary."""
        status_str = data.get("status", "error")
        try:
            status = InferenceStatus(status_str)
        except ValueError:
            status = InferenceStatus.ERROR
        
        return cls(
            pr_id=data["pr_id"],
            status=status,
            detected_bugs=data.get("detected_bugs", []),
            error_message=data.get("error_message"),
            latency_seconds=data.get("latency_seconds", 0.0),
            tokens_used=data.get("tokens_used", 0),
            model_id=data.get("model_id"),
            metadata=data.get("metadata", {})
        )

    def add_bug_detection(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        severity: Severity,
        description: str
    ) -> None:
        """Add a detected bug to the response."""
        self.detected_bugs.append({
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "severity": severity.value,
            "description": description
        })
