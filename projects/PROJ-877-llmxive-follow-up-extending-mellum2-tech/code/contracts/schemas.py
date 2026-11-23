"""
Base entity schemas for the llmXive automated science pipeline.

Defines strict data structures for CodeChunk, Threshold, and CorrelationResult
with explicit field definitions, type validation, and serialization methods.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime
import hashlib
import re


@dataclass
class CodeChunk:
    """
    Represents a single code chunk extracted from a repository.
    
    Fields:
        chunk_id: Unique identifier for the chunk (hash of content + repo path).
        repo_id: Identifier of the source repository (e.g., 'username/repo').
        file_path: Relative path of the file within the repository.
        language: Programming language (e.g., 'python', 'java').
        content: The raw source code text.
        start_line: 1-based starting line number in the original file.
        end_line: 1-based ending line number in the original file.
        cyclomatic_complexity: Calculated cyclomatic complexity metric.
        nesting_depth: Maximum nesting depth of control structures.
        repetition_ratio: Ratio of repeated code patterns (0.0 to 1.0).
        token_count: Number of tokens in the chunk (after tokenization).
        processed_at: ISO format timestamp of processing.
        metadata: Additional arbitrary key-value pairs.
    """
    chunk_id: str
    repo_id: str
    file_path: str
    language: str
    content: str
    start_line: int
    end_line: int
    cyclomatic_complexity: int
    nesting_depth: int
    repetition_ratio: float
    token_count: int
    processed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate fields and generate chunk_id if missing."""
        if not self.chunk_id:
            # Generate deterministic ID based on content and location
            content_hash = hashlib.sha256(self.content.encode('utf-8')).hexdigest()[:16]
            path_hash = hashlib.sha256(f"{self.repo_id}:{self.file_path}".encode('utf-8')).hexdigest()[:8]
            self.chunk_id = f"ch_{path_hash}_{content_hash}"
        
        if not re.match(r'^[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+$', self.repo_id):
            raise ValueError(f"Invalid repo_id format: {self.repo_id}")
        
        if self.language not in ('python', 'java', 'javascript', 'cpp', 'go'):
            raise ValueError(f"Unsupported language: {self.language}")
        
        if not (0.0 <= self.repetition_ratio <= 1.0):
            raise ValueError(f"repetition_ratio must be between 0.0 and 1.0, got {self.repetition_ratio}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeChunk':
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'CodeChunk':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Threshold:
    """
    Represents a detected structural threshold where the relationship
    between complexity and prediction loss shifts.
    
    Fields:
        threshold_id: Unique identifier for this threshold detection.
        metric_name: The complexity metric being analyzed (e.g., 'cyclomatic_complexity').
        threshold_value: The numeric value where the shift occurs.
        confidence_score: Statistical confidence (0.0 to 1.0) of the threshold detection.
        model_type: Type of model used for detection ('piecewise_linear', 'change_point').
        segment_stats: Dictionary containing statistics for segments before/after threshold.
        detected_at: ISO format timestamp of detection.
        context: Additional context about the detection (e.g., language, dataset subset).
    """
    threshold_id: str
    metric_name: str
    threshold_value: float
    confidence_score: float
    model_type: str
    segment_stats: Dict[str, Any]
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate fields."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {self.confidence_score}")
        
        if self.model_type not in ('piecewise_linear', 'change_point', 'spline'):
            raise ValueError(f"Unsupported model_type: {self.model_type}")
        
        if self.threshold_id is None or self.threshold_id.strip() == "":
            self.threshold_id = f"th_{int(datetime.utcnow().timestamp())}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Threshold':
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Threshold':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class CorrelationResult:
    """
    Represents the result of a correlation analysis between complexity metrics
    and LLM prediction loss.
    
    Fields:
        result_id: Unique identifier for this result.
        metric_name: The complexity metric analyzed.
        loss_type: Type of loss analyzed ('token_loss', 'entropy', 'normalized_loss').
        correlation_coefficient: Pearson or Spearman correlation value (-1.0 to 1.0).
        correlation_method: 'pearson' or 'spearman'.
        p_value: Statistical significance p-value.
        sample_size: Number of data points used in the analysis.
        confidence_interval: Tuple (lower, upper) for 95% CI of correlation.
        language: Language subset analyzed (e.g., 'python', 'java').
        computed_at: ISO format timestamp of computation.
        metadata: Additional analysis metadata (e.g., model used, dataset version).
    """
    result_id: str
    metric_name: str
    loss_type: str
    correlation_coefficient: float
    correlation_method: str
    p_value: float
    sample_size: int
    confidence_interval: List[float]
    language: str
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate fields."""
        if not -1.0 <= self.correlation_coefficient <= 1.0:
            raise ValueError(f"correlation_coefficient must be between -1.0 and 1.0, got {self.correlation_coefficient}")
        
        if self.correlation_method not in ('pearson', 'spearman'):
            raise ValueError(f"Unsupported correlation_method: {self.correlation_method}")
        
        if not (0.0 <= self.p_value <= 1.0):
            raise ValueError(f"p_value must be between 0.0 and 1.0, got {self.p_value}")
        
        if len(self.confidence_interval) != 2:
            raise ValueError(f"confidence_interval must have 2 elements, got {len(self.confidence_interval)}")
        
        if self.result_id is None or self.result_id.strip() == "":
            self.result_id = f"cr_{int(datetime.utcnow().timestamp())}_{hash(self.metric_name + self.loss_type) % 10000}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrelationResult':
        """Create instance from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'CorrelationResult':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if the correlation is statistically significant."""
        return self.p_value < alpha