"""
Base entity schemas for the llmXive pipeline.
Defines strict data contracts for CodeChunk, Threshold, and CorrelationResult.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime
import hashlib
import re
from pathlib import Path


@dataclass
class CodeChunk:
    """
    Schema for a single code chunk extracted from a repository.
    Used as the fundamental unit of analysis in the pipeline.
    """
    chunk_id: str
    repository: str
    file_path: str
    language: str
    content: str
    start_line: int
    end_line: int
    
    # Static Analysis Metrics (populated by T016)
    cyclomatic_complexity: Optional[float] = None
    nesting_depth: Optional[int] = None
    repetition_ratio: Optional[float] = None
    lines_of_code: Optional[int] = None
    token_count: Optional[int] = None
    
    # Inference Metrics (populated by T017)
    token_loss: Optional[float] = None
    entropy: Optional[float] = None
    normalized_loss: Optional[float] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Validate and compute checksum if not present."""
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty")
        
        if not self.language:
            raise ValueError("language cannot be empty")
        
        if not self.content:
            raise ValueError("content cannot be empty")
        
        # Auto-generate checksum if missing
        if not self.checksum:
            content_hash = hashlib.sha256(
                f"{self.repository}:{self.file_path}:{self.start_line}:{self.end_line}".encode('utf-8')
            ).hexdigest()
            self.checksum = content_hash
        
        # Validate chunk_id format (must be alphanumeric with underscores/dashes)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.chunk_id):
            raise ValueError(f"Invalid chunk_id format: {self.chunk_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunk_id": self.chunk_id,
            "repository": self.repository,
            "file_path": self.file_path,
            "language": self.language,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "nesting_depth": self.nesting_depth,
            "repetition_ratio": self.repetition_ratio,
            "lines_of_code": self.lines_of_code,
            "token_count": self.token_count,
            "token_loss": self.token_loss,
            "entropy": self.entropy,
            "normalized_loss": self.normalized_loss,
            "created_at": self.created_at,
            "checksum": self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeChunk":
        """Create instance from dictionary."""
        required_fields = ["chunk_id", "repository", "file_path", "language", "content", "start_line", "end_line"]
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"Missing required field: {field_name}")
        
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CodeChunk":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class Threshold:
    """
    Schema for a detected threshold point in the complexity-loss relationship.
    Represents a structural break where the correlation behavior changes.
    """
    threshold_id: str
    metric_name: str  # e.g., "cyclomatic_complexity", "nesting_depth"
    threshold_value: float
    model_type: str  # "linear", "piecewise", "exponential"
    breakpoint_position: float  # Normalized position (0.0 to 1.0)
    
    # Statistical properties
    pre_threshold_correlation: Optional[float] = None
    post_threshold_correlation: Optional[float] = None
    pre_threshold_slope: Optional[float] = None
    post_threshold_slope: Optional[float] = None
    
    # Model comparison
    aic_linear: Optional[float] = None
    aic_piecewise: Optional[float] = None
    bic_linear: Optional[float] = None
    bic_piecewise: Optional[float] = None
    model_preference: Optional[str] = None  # "linear" or "piecewise"
    
    # Sensitivity analysis
    sensitivity_shift: Optional[float] = None
    bootstrap_std: Optional[float] = None
    
    # Metadata
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    dataset_split: Optional[str] = None  # "python", "java", or "combined"
    
    def __post_init__(self):
        """Validate threshold properties."""
        if not self.threshold_id:
            raise ValueError("threshold_id cannot be empty")
        
        if not self.metric_name:
            raise ValueError("metric_name cannot be empty")
        
        if self.threshold_value is None:
            raise ValueError("threshold_value cannot be None")
        
        if self.model_type not in ["linear", "piecewise", "exponential"]:
            raise ValueError(f"Invalid model_type: {self.model_type}")
        
        if self.breakpoint_position is not None and not (0.0 <= self.breakpoint_position <= 1.0):
            raise ValueError(f"breakpoint_position must be between 0.0 and 1.0, got {self.breakpoint_position}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "threshold_id": self.threshold_id,
            "metric_name": self.metric_name,
            "threshold_value": self.threshold_value,
            "model_type": self.model_type,
            "breakpoint_position": self.breakpoint_position,
            "pre_threshold_correlation": self.pre_threshold_correlation,
            "post_threshold_correlation": self.post_threshold_correlation,
            "pre_threshold_slope": self.pre_threshold_slope,
            "post_threshold_slope": self.post_threshold_slope,
            "aic_linear": self.aic_linear,
            "aic_piecewise": self.aic_piecewise,
            "bic_linear": self.bic_linear,
            "bic_piecewise": self.bic_piecewise,
            "model_preference": self.model_preference,
            "sensitivity_shift": self.sensitivity_shift,
            "bootstrap_std": self.bootstrap_std,
            "detected_at": self.detected_at,
            "dataset_split": self.dataset_split
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Threshold":
        """Create instance from dictionary."""
        required_fields = ["threshold_id", "metric_name", "threshold_value", "model_type"]
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"Missing required field: {field_name}")
        
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Threshold":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class CorrelationResult:
    """
    Schema for correlation analysis results between complexity metrics and prediction loss.
    """
    result_id: str
    metric_name: str  # e.g., "cyclomatic_complexity"
    loss_metric: str  # e.g., "token_loss", "normalized_loss"
    dataset_split: str  # "python", "java", or "combined"
    
    # Correlation coefficients
    pearson_r: Optional[float] = None
    pearson_p: Optional[float] = None
    spearman_rho: Optional[float] = None
    spearman_p: Optional[float] = None
    
    # Regression statistics
    slope: Optional[float] = None
    intercept: Optional[float] = None
    r_squared: Optional[float] = None
    n_samples: int = 0
    
    # Statistical significance
    is_significant: bool = False
    significance_level: float = 0.05
    confidence_interval_95: Optional[List[float]] = None
    
    # Cross-language comparison
    cross_language_diff: Optional[float] = None
    cross_language_significant: Optional[bool] = None
    
    # Metadata
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    analysis_version: str = "1.0.0"
    
    def __post_init__(self):
        """Validate correlation result."""
        if not self.result_id:
            raise ValueError("result_id cannot be empty")
        
        if not self.metric_name:
            raise ValueError("metric_name cannot be empty")
        
        if not self.loss_metric:
            raise ValueError("loss_metric cannot be empty")
        
        if not self.dataset_split:
            raise ValueError("dataset_split cannot be empty")
        
        if self.n_samples < 0:
            raise ValueError("n_samples cannot be negative")
        
        # Validate correlation coefficients if present
        if self.pearson_r is not None and not (-1.0 <= self.pearson_r <= 1.0):
            raise ValueError(f"pearson_r must be between -1.0 and 1.0, got {self.pearson_r}")
        
        if self.spearman_rho is not None and not (-1.0 <= self.spearman_rho <= 1.0):
            raise ValueError(f"spearman_rho must be between -1.0 and 1.0, got {self.spearman_rho}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "result_id": self.result_id,
            "metric_name": self.metric_name,
            "loss_metric": self.loss_metric,
            "dataset_split": self.dataset_split,
            "pearson_r": self.pearson_r,
            "pearson_p": self.pearson_p,
            "spearman_rho": self.spearman_rho,
            "spearman_p": self.spearman_p,
            "slope": self.slope,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "n_samples": self.n_samples,
            "is_significant": self.is_significant,
            "significance_level": self.significance_level,
            "confidence_interval_95": self.confidence_interval_95,
            "cross_language_diff": self.cross_language_diff,
            "cross_language_significant": self.cross_language_significant,
            "computed_at": self.computed_at,
            "analysis_version": self.analysis_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrelationResult":
        """Create instance from dictionary."""
        required_fields = ["result_id", "metric_name", "loss_metric", "dataset_split", "n_samples"]
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"Missing required field: {field_name}")
        
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CorrelationResult":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)