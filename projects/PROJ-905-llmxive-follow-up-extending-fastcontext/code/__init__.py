"""
llmXive: Extended FastContext Research Pipeline.

This package provides data models, schema definitions, and utilities
for analyzing repository structural regularity and FastContext performance.
"""

from typing import Dict, List, Optional, Any

# --- Data Models ---

class RepositoryMetadata:
    """Represents metadata for a single repository in the dataset."""
    
    def __init__(
        self,
        repo_id: str,
        issue_id: str,
        ground_truth_file_paths: Optional[List[str]] = None,
        regularity_score: Optional[float] = None,
        split: Optional[str] = None
    ):
        self.repo_id = repo_id
        self.issue_id = issue_id
        self.ground_truth_file_paths = ground_truth_file_paths or []
        self.regularity_score = regularity_score
        self.split = split  # 'regular', 'irregular', or None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_id": self.repo_id,
            "issue_id": self.issue_id,
            "ground_truth_file_paths": self.ground_truth_file_paths,
            "regularity_score": self.regularity_score,
            "split": self.split
        }

class ExplorationLog:
    """Represents a single run log entry for FastContext execution."""
    
    def __init__(
        self,
        repo_id: str,
        issue_id: str,
        model_name: str,
        context_precision: float,
        total_tokens: int,
        wall_clock_latency_ms: float,
        exploration_latency_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        self.repo_id = repo_id
        self.issue_id = issue_id
        self.model_name = model_name
        self.context_precision = context_precision
        self.total_tokens = total_tokens
        self.wall_clock_latency_ms = wall_clock_latency_ms
        self.exploration_latency_ms = exploration_latency_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_id": self.repo_id,
            "issue_id": self.issue_id,
            "model_name": self.model_name,
            "context_precision": self.context_precision,
            "total_tokens": self.total_tokens,
            "wall_clock_latency_ms": self.wall_clock_latency_ms,
            "exploration_latency_ms": self.exploration_latency_ms,
            "error": self.error
        }

class StatisticalSummary:
    """Aggregated statistical results from comparative analysis."""
    
    def __init__(
        self,
        p_value: float,
        cohen_d: float,
        degradation_percent: float,
        boundary_threshold: float,
        regression_slope: float,
        r_squared: float
    ):
        self.p_value = p_value
        self.cohen_d = cohen_d
        self.degradation_percent = degradation_percent
        self.boundary_threshold = boundary_threshold
        self.regression_slope = regression_slope
        self.r_squared = r_squared

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p_value": self.p_value,
            "effect_size": {"cohen_d": self.cohen_d},
            "degradation_percent": self.degradation_percent,
            "boundary_threshold": self.boundary_threshold,
            "regression_slope": self.regression_slope,
            "r_squared": self.r_squared
        }

# --- Schema Definitions (Dict Type Hints for JSON/CSV) ---

# Schema for data/raw/ground_truth_annotations.csv
GROUND_TRUTH_SCHEMA = {
    "repo_id": str,
    "issue_id": str,
    "ground_truth_file_paths": list  # Will be serialized as JSON string in CSV
}

# Schema for data/processed/regularity_scores.csv
REGULARITY_SCORES_SCHEMA = {
    "repo_id": str,
    "regularity_score": float,
    "split": str  # 'regular' or 'irregular'
}

# Schema for data/results/exploration_logs.jsonl
EXPLORATION_LOG_SCHEMA = {
    "repo_id": str,
    "issue_id": str,
    "model_name": str,
    "context_precision": float,
    "total_tokens": int,
    "wall_clock_latency_ms": float,
    "exploration_latency_ms": float,
    "error": str
}

# Schema for data/results/statistical_summary.json
STATISTICAL_SUMMARY_SCHEMA = {
    "p_value": float,
    "effect_size": dict,  # {"cohen_d": float}
    "degradation_percent": float,
    "boundary_threshold": float,
    "regression_slope": float,
    "r_squared": float
}
