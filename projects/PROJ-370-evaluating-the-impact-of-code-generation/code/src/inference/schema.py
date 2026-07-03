from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json

from code.src.extraction.schema import Severity
from code.src.detection.schema import LLMCodeDetectionResult

class InferenceStatus(Enum):
    """Status of an inference request."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    MEMORY_EXCEEDED = "memory_exceeded"

@dataclass
class InferenceRequest:
    """
    Represents a request to run inference on a specific code snippet or PR diff.
    Corresponds to T008: Define data classes in src/inference/schema.py.
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    diff_content: str
    llm_code_flag: bool
    context_window_limit: int = 4096
    max_tokens: int = 512
    temperature: float = 0.0
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the request to a dictionary for serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "diff_content": self.diff_content,
            "llm_code_flag": self.llm_code_flag,
            "context_window_limit": self.context_window_limit,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "request_id": self.request_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InferenceRequest':
        """Create an InferenceRequest from a dictionary."""
        return cls(
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            diff_content=data["diff_content"],
            llm_code_flag=data["llm_code_flag"],
            context_window_limit=data.get("context_window_limit", 4096),
            max_tokens=data.get("max_tokens", 512),
            temperature=data.get("temperature", 0.0),
            request_id=data.get("request_id")
        )

@dataclass
class InferenceResponse:
    """
    Represents the response from an LLM inference run.
    Includes detected bugs, severity, and metadata about the run.
    """
    request_id: Optional[str]
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    status: InferenceStatus
    detected_bugs: List[Dict[str, Any]] = field(default_factory=list)
    raw_output: Optional[str] = None
    error_message: Optional[str] = None
    latency_seconds: Optional[float] = None
    tokens_generated: Optional[int] = None
    model_name: str = "starcoder2-3b"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "status": self.status.value,
            "detected_bugs": self.detected_bugs,
            "raw_output": self.raw_output,
            "error_message": self.error_message,
            "latency_seconds": self.latency_seconds,
            "tokens_generated": self.tokens_generated,
            "model_name": self.model_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InferenceResponse':
        """Create an InferenceResponse from a dictionary."""
        return cls(
            request_id=data.get("request_id"),
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            status=InferenceStatus(data["status"]),
            detected_bugs=data.get("detected_bugs", []),
            raw_output=data.get("raw_output"),
            error_message=data.get("error_message"),
            latency_seconds=data.get("latency_seconds"),
            tokens_generated=data.get("tokens_generated"),
            model_name=data.get("model_name", "starcoder2-3b")
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize the response to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> 'InferenceResponse':
        """Deserialize a JSON string to an InferenceResponse."""
        return cls.from_dict(json.loads(json_str))
