"""
Core entity schemas for the llmXive research pipeline.
Defines dataclasses for CodeChunk, Threshold, and CorrelationResult.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import hashlib
import re

@dataclass
class CodeChunk:
    """
    Represents a single parsed code chunk extracted from a repository.
    Used as the primary unit of analysis for complexity and inference.
    """
    chunk_id: str
    repo_name: str
    file_path: str
    language: str  # 'python' or 'java'
    content: str
    start_line: int
    end_line: int
    complexity_metrics: Dict[str, float] = field(default_factory=dict)
    # Metrics populated by T016 (Preprocess): cyclomatic_complexity, nesting_depth, repetition_ratio, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "repo_name": self.repo_name,
            "file_path": self.file_path,
            "language": self.language,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "complexity_metrics": self.complexity_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeChunk':
        return cls(
            chunk_id=data["chunk_id"],
            repo_name=data["repo_name"],
            file_path=data["file_path"],
            language=data["language"],
            content=data["content"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            complexity_metrics=data.get("complexity_metrics", {})
        )

    def generate_id(self) -> str:
        """Generate a deterministic ID based on repo, file, and line range."""
        raw = f"{self.repo_name}:{self.file_path}:{self.start_line}-{self.end_line}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


@dataclass
class Threshold:
    """
    Represents a detected structural threshold where the complexity-loss relationship shifts.
    Used in User Story 2 (Non-Linear Threshold Detection).
    """
    metric_name: str
    threshold_value: float
    model_preference: str  # 'linear' or 'piecewise'
    aic_linear: float
    aic_piecewise: float
    bic_linear: float
    bic_piecewise: float
    confidence_interval: List[float] = field(default_factory=lambda: [0.0, 0.0])
    sensitivity_shift: float = 0.0  # From bootstrapping (SC-002)
    detection_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "threshold_value": self.threshold_value,
            "model_preference": self.model_preference,
            "aic_linear": self.aic_linear,
            "aics_piecewise": self.aic_piecewise,
            "bic_linear": self.bic_linear,
            "bic_piecewise": self.bic_piecewise,
            "confidence_interval": self.confidence_interval,
            "sensitivity_shift": self.sensitivity_shift,
            "detection_timestamp": self.detection_timestamp
        }


@dataclass
class CorrelationResult:
    """
    Represents the statistical correlation between complexity metrics and LLM prediction loss.
    Used in User Story 1 (Correlation Analysis).
    """
    metric_name: str
    language: str  # 'python' or 'java' or 'all'
    pearson_r: float
    pearson_pvalue: float
    spearman_r: float
    spearman_pvalue: float
    n_samples: int
    normalized_loss_mean: float
    normalized_loss_std: float
    complexity_mean: float
    complexity_std: float
    analysis_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "language": self.language,
            "pearson_r": self.pearson_r,
            "pearson_pvalue": self.pearson_pvalue,
            "spearman_r": self.spearman_r,
            "spearman_pvalue": self.spearman_pvalue,
            "n_samples": self.n_samples,
            "normalized_loss_mean": self.normalized_loss_mean,
            "normalized_loss_std": self.normalized_loss_std,
            "complexity_mean": self.complexity_mean,
            "complexity_std": self.complexity_std,
            "analysis_timestamp": self.analysis_timestamp
        }