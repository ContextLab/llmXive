"""
Threshold Schema Definitions for US3 - Anomaly Score Threshold Calibration.

This module defines the data structures used for threshold calibration
as specified in User Story 3 acceptance criteria.

Per Constitution Principle I (API Consistency), these schemas must match
the service interface contracts defined in spec.md.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import numpy as np


@dataclass
class ThresholdConfig:
    """
    Configuration for threshold calibration service.

    Per FR-009 and US3 acceptance criteria:
    - Percentile-based threshold calibration
    - Adaptive boundary updates for streaming mode
    - Configurable confidence levels
    """
    # Primary calibration method
    method: str = "percentile"  # Options: "percentile", "adaptive", "fixed"

    # Percentile-based parameters
    percentile: float = 95.0  # Target percentile for threshold (0-100)
    confidence_level: float = 0.95  # Confidence level for threshold bounds

    # Adaptive mode parameters
    adaptive_enabled: bool = True
    update_frequency: int = 100  # Number of observations between updates
    min_observations: int = 50  # Minimum observations before first calibration

    # Boundary parameters
    lower_bound_percentile: float = 5.0
    upper_bound_percentile: float = 99.0
    min_threshold: float = 0.0  # Absolute minimum threshold
    max_threshold: float = 100.0  # Absolute maximum threshold

    # Streaming parameters
    decay_factor: float = 0.9  # Exponential decay for streaming updates
    window_size: Optional[int] = None  # Rolling window size (None = all history)

    # Logging
    log_calibration_events: bool = True

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0 <= self.percentile <= 100:
            raise ValueError(f"percentile must be between 0 and 100, got {self.percentile}")
        if not 0 < self.confidence_level <= 1:
            raise ValueError(f"confidence_level must be between 0 and 1, got {self.confidence_level}")
        if not 0 < self.decay_factor <= 1:
            raise ValueError(f"decay_factor must be between 0 and 1, got {self.decay_factor}")
        if self.min_observations < 1:
            raise ValueError(f"min_observations must be >= 1, got {self.min_observations}")
        if self.update_frequency < 1:
            raise ValueError(f"update_frequency must be >= 1, got {self.update_frequency}")


@dataclass
class ThresholdState:
    """
    Current state of threshold calibration.

    Per Constitution Principle III, this state must be persisted to the
    state file for reproducibility.
    """
    # Current threshold value
    current_threshold: float = 0.0

    # Threshold bounds
    lower_bound: float = 0.0
    upper_bound: float = 1.0

    # Calibration statistics
    calibration_count: int = 0
    total_observations: int = 0
    last_calibration_time: Optional[datetime] = None

    # Historical thresholds (for debugging/analysis)
    threshold_history: List[float] = field(default_factory=list)

    # Score distribution statistics
    score_mean: Optional[float] = None
    score_std: Optional[float] = None
    score_percentiles: Dict[int, float] = field(default_factory=dict)

    # Calibration metadata
    method_used: str = "percentile"
    config_hash: Optional[str] = None  # SHA256 of config for reproducibility

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "current_threshold": self.current_threshold,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "calibration_count": self.calibration_count,
            "total_observations": self.total_observations,
            "last_calibration_time": self.last_calibration_time.isoformat() if self.last_calibration_time else None,
            "threshold_history": self.threshold_history,
            "score_mean": self.score_mean,
            "score_std": self.score_std,
            "score_percentiles": self.score_percentiles,
            "method_used": self.method_used,
            "config_hash": self.config_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThresholdState":
        """Create state from dictionary."""
        last_cal_time = None
        if data.get("last_calibration_time"):
            last_cal_time = datetime.fromisoformat(data["last_calibration_time"])

        return cls(
            current_threshold=data.get("current_threshold", 0.0),
            lower_bound=data.get("lower_bound", 0.0),
            upper_bound=data.get("upper_bound", 1.0),
            calibration_count=data.get("calibration_count", 0),
            total_observations=data.get("total_observations", 0),
            last_calibration_time=last_cal_time,
            threshold_history=data.get("threshold_history", []),
            score_mean=data.get("score_mean"),
            score_std=data.get("score_std"),
            score_percentiles=data.get("score_percentiles", {}),
            method_used=data.get("method_used", "percentile"),
            config_hash=data.get("config_hash")
        )


@dataclass
class CalibrationResult:
    """
    Result of a threshold calibration operation.

    Per US3 acceptance criteria, this must include:
    - New threshold value
    - Confidence bounds
    - Statistics about the calibration
    """
    # Threshold values
    threshold: float
    lower_bound: float
    upper_bound: float

    # Calibration metadata
    method: str
    confidence_level: float
    calibration_time: datetime

    # Score distribution info
    score_count: int
    score_mean: float
    score_std: float
    score_percentiles: Dict[int, float]

    # Quality metrics
    calibration_quality: str  # "good", "fair", "poor"
    warning_messages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "threshold": self.threshold,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "method": self.method,
            "confidence_level": self.confidence_level,
            "calibration_time": self.calibration_time.isoformat(),
            "score_count": self.score_count,
            "score_mean": self.score_mean,
            "score_std": self.score_std,
            "score_percentiles": self.score_percentiles,
            "calibration_quality": self.calibration_quality,
            "warning_messages": self.warning_messages
        }


@dataclass
class ThresholdUpdate:
    """
    Represents a threshold update event for streaming mode.

    Per US3 acceptance criteria for streaming updates.
    """
    timestamp: datetime
    old_threshold: float
    new_threshold: float
    update_reason: str  # "periodic", "adaptive", "manual"
    observations_since_update: int
    score_stats: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert update to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "old_threshold": self.old_threshold,
            "new_threshold": self.new_threshold,
            "update_reason": self.update_reason,
            "observations_since_update": self.observations_since_update,
            "score_stats": self.score_stats
        }
