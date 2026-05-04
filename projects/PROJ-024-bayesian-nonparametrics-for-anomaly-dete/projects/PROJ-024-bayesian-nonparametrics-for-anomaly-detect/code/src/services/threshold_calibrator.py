"""
ThresholdCalibratorService - Service for unsupervised threshold calibration.

Implements all 6 required methods per spec.md Service Interfaces section.
Type hints added per PEP 484 compliance (T161).
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import (
    Optional,
    List,
    Dict,
    Any,
    Union,
    Tuple,
    Sequence,
    Literal,
)
import numpy as np
import logging
import json

from models.anomaly_score import AnomalyScore
from evaluation.metrics import EvaluationMetrics


@dataclass
class CalibrationResult:
    """Result container for threshold calibration operations."""
    timestamp: datetime
    method: str
    threshold: float
    percentile_used: float
    score_statistics: Dict[str, float] = field(default_factory=dict)
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThresholdConfig:
    """Configuration for threshold calibration."""
    method: Literal["percentile", "mad", "iqr", "adaptive"] = "percentile"
    percentile: float = 95.0
    mad_factor: float = 3.0
    iqr_multiplier: float = 1.5
    min_samples: int = 100
    max_samples: int = 10000
    update_frequency: int = 1000
    decay_factor: float = 0.95


class ThresholdCalibratorService:
    """
    Service interface for unsupervised threshold calibration.
    
    Implements exactly 6 required methods per spec.md Service Interfaces:
    1. initialize
    2. calibrate
    3. update_threshold
    4. get_current_threshold
    5. get_calibration_history
    6. save_calibration_state
    """

    def __init__(
        self,
        config: Optional[ThresholdConfig] = None,
        log_level: int = logging.INFO
    ) -> None:
        """
        Initialize the ThresholdCalibratorService.
        
        Args:
            config: Configuration for threshold calibration
            log_level: Logging level for the service
        """
        self.config: ThresholdConfig = config or ThresholdConfig()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        self._current_threshold: Optional[float] = None
        self._score_buffer: List[float] = []
        self._calibration_history: List[CalibrationResult] = []
        self._total_observations: int = 0
        self._last_update_index: int = 0
        self._running_mean: float = 0.0
        self._running_std: float = 0.0

    def initialize(self) -> bool:
        """
        Initialize the calibration service.
        
        Returns:
            True if initialization successful
        """
        try:
            self._score_buffer = []
            self._calibration_history = []
            self._total_observations = 0
            self._last_update_index = 0
            self._running_mean = 0.0
            self._running_std = 0.0
            self._current_threshold = None
            
            self.logger.info("ThresholdCalibratorService initialized")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def calibrate(
        self,
        scores: Union[np.ndarray, List[float]],
        method: Optional[str] = None
    ) -> CalibrationResult:
        """
        Calibrate threshold using the specified method.
        
        Args:
            scores: Anomaly scores to calibrate against
            method: Calibration method override (percentile, mad, iqr, adaptive)
        
        Returns:
            CalibrationResult with computed threshold and statistics
        """
        try:
            # Convert to numpy array
            if isinstance(scores, list):
                scores_array: np.ndarray = np.array(scores)
            else:
                scores_array = scores
            
            if len(scores_array) < self.config.min_samples:
                self.logger.warning(
                    f"Insufficient samples ({len(scores_array)} < {self.config.min_samples})"
                )
                # Return default threshold
                default_threshold: float = 0.7
                self._current_threshold = default_threshold
                return CalibrationResult(
                    timestamp=datetime.now(),
                    method="default",
                    threshold=default_threshold,
                    percentile_used=0.0,
                    score_statistics={}
                )
            
            # Limit buffer size
            max_samples: int = min(len(scores_array), self.config.max_samples)
            if len(scores_array) > max_samples:
                # Use percentile of largest values
                scores_array = np.sort(scores_array)[-max_samples:]
            
            # Select method
            calibration_method: str = method or self.config.method
            
            # Compute threshold based on method
            if calibration_method == "percentile":
                threshold, stats = self._calibrate_percentile(scores_array)
            elif calibration_method == "mad":
                threshold, stats = self._calibrate_mad(scores_array)
            elif calibration_method == "iqr":
                threshold, stats = self._calibrate_iqr(scores_array)
            elif calibration_method == "adaptive":
                threshold, stats = self._calibrate_adaptive(scores_array)
            else:
                self.logger.warning(f"Unknown method {calibration_method}, using percentile")
                threshold, stats = self._calibrate_percentile(scores_array)
            
            # Update current threshold
            self._current_threshold = threshold
            
            # Create result
            result: CalibrationResult = CalibrationResult(
                timestamp=datetime.now(),
                method=calibration_method,
                threshold=threshold,
                percentile_used=self.config.percentile,
                score_statistics=stats,
                metadata={
                    "n_samples": len(scores_array),
                    "total_observations": self._total_observations
                }
            )
            
            self._calibration_history.append(result)
            self.logger.info(
                f"Calibration complete: threshold={threshold:.4f}, "
                f"method={calibration_method}"
            )
            return result
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            raise

    def update_threshold(
        self,
        new_score: float,
        force_update: bool = False
    ) -> Optional[float]:
        """
        Update threshold based on a new observation.
        
        Args:
            new_score: New anomaly score to incorporate
            force_update: Force update regardless of frequency settings
        
        Returns:
            Updated threshold or None if not updated
        """
        try:
            # Add score to buffer
            self._score_buffer.append(new_score)
            self._total_observations += 1
            
            # Update running statistics
            self._update_running_stats(new_score)
            
            # Check if we should update
            should_update: bool = (
                force_update or
                (self._total_observations - self._last_update_index) >= self.config.update_frequency
            )
            
            if should_update and len(self._score_buffer) >= self.config.min_samples:
                # Perform calibration
                scores_array: np.ndarray = np.array(self._score_buffer[-self.config.max_samples:])
                self.calibrate(scores_array)
                self._last_update_index = self._total_observations
                return self._current_threshold
            
            return self._current_threshold
        except Exception as e:
            self.logger.error(f"Threshold update failed: {e}")
            return self._current_threshold

    def get_current_threshold(self) -> Optional[float]:
        """
        Get the current threshold value.
        
        Returns:
            Current threshold or None if not yet calibrated
        """
        return self._current_threshold

    def get_calibration_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the calibration history.
        
        Args:
            limit: Maximum number of history entries to return
        
        Returns:
            List of calibration result dictionaries
        """
        history: List[Dict[str, Any]] = []
        results: List[CalibrationResult] = (
            self._calibration_history[-limit:] if limit else self._calibration_history
        )
        
        for result in results:
            history.append({
                "timestamp": result.timestamp.isoformat(),
                "method": result.method,
                "threshold": result.threshold,
                "percentile_used": result.percentile_used,
                "score_statistics": result.score_statistics,
                "confidence_interval": result.confidence_interval,
                "metadata": result.metadata
            })
        
        return history

    def save_calibration_state(
        self,
        output_path: Path
    ) -> bool:
        """
        Save calibration state to a file.
        
        Args:
            output_path: Path to save the calibration state
        
        Returns:
            True if save successful
        """
        try:
            state: Dict[str, Any] = {
                "config": {
                    "method": self.config.method,
                    "percentile": self.config.percentile,
                    "mad_factor": self.config.mad_factor,
                    "iqr_multiplier": self.config.iqr_multiplier,
                    "min_samples": self.config.min_samples,
                    "max_samples": self.config.max_samples,
                    "update_frequency": self.config.update_frequency,
                    "decay_factor": self.config.decay_factor
                },
                "current_threshold": self._current_threshold,
                "total_observations": self._total_observations,
                "last_update_index": self._last_update_index,
                "running_mean": self._running_mean,
                "running_std": self._running_std,
                "history": self.get_calibration_history(),
                "saved_at": datetime.now().isoformat()
            }
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write state
            with open(output_path, "w") as f:
                json.dump(state, f, indent=2)
            
            self.logger.info(f"Calibration state saved to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save calibration state: {e}")
            return False

    # Private helper methods

    def _calibrate_percentile(self, scores: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Calibrate threshold using percentile method."""
        threshold: float = float(np.percentile(scores, self.config.percentile))
        stats: Dict[str, float] = {
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "median": float(np.median(scores))
        }
        return threshold, stats

    def _calibrate_mad(self, scores: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Calibrate threshold using Median Absolute Deviation (MAD)."""
        median: float = float(np.median(scores))
        mad: float = float(np.median(np.abs(scores - median)))
        threshold: float = median + self.config.mad_factor * mad * 1.4826
        
        stats: Dict[str, float] = {
            "median": median,
            "mad": mad,
            "factor": self.config.mad_factor
        }
        return threshold, stats

    def _calibrate_iqr(self, scores: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Calibrate threshold using Interquartile Range (IQR)."""
        q1: float = float(np.percentile(scores, 25))
        q3: float = float(np.percentile(scores, 75))
        iqr: float = q3 - q1
        threshold: float = q3 + self.config.iqr_multiplier * iqr
        
        stats: Dict[str, float] = {
            "q1": q1,
            "q3": q3,
            "iqr": iqr
        }
        return threshold, stats

    def _calibrate_adaptive(self, scores: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Calibrate threshold using adaptive method with decay."""
        # Combine percentile with running statistics
        percentile_threshold: float = float(np.percentile(scores, self.config.percentile))
        
        if self._running_std > 0:
            adaptive_threshold: float = self._running_mean + 3 * self._running_std
            # Blend percentile and adaptive
            threshold: float = (
                0.7 * percentile_threshold +
                0.3 * adaptive_threshold
            )
        else:
            threshold = percentile_threshold
        
        stats: Dict[str, float] = {
            "running_mean": self._running_mean,
            "running_std": self._running_std,
            "percentile_threshold": percentile_threshold
        }
        return threshold, stats

    def _update_running_stats(self, score: float) -> None:
        """Update running mean and standard deviation."""
        n: int = self._total_observations
        
        # Welford's online algorithm for numerical stability
        delta: float = score - self._running_mean
        self._running_mean += delta / n
        delta2: float = score - self._running_mean
        # For simplicity, track sum of squared differences
        # In production, use full Welford's algorithm with M2
        
        # Simple exponential moving average for variance
        if n > 1:
            variance: float = (1 - self.config.decay_factor) * (delta ** 2) + \
                             self.config.decay_factor * (self._running_std ** 2)
            self._running_std = np.sqrt(max(variance, 1e-10))


def create_calibrator(
    config: Optional[ThresholdConfig] = None
) -> ThresholdCalibratorService:
    """
    Factory function to create a ThresholdCalibratorService instance.
    
    Args:
        config: Optional configuration for the calibrator
    
    Returns:
        Configured ThresholdCalibratorService instance
    """
    return ThresholdCalibratorService(config=config)


def main() -> None:
    """Main entry point for service demonstration/testing."""
    import sys
    
    # Create calibrator
    config: ThresholdConfig = ThresholdConfig(
        method="percentile",
        percentile=95.0,
        min_samples=50
    )
    calibrator: ThresholdCalibratorService = create_calibrator(config=config)
    
    # Initialize
    if not calibrator.initialize():
        print("Failed to initialize calibrator")
        sys.exit(1)
    
    # Generate synthetic scores for testing
    np.random.seed(42)
    scores: np.ndarray = np.concatenate([
        np.random.normal(0.3, 0.1, 900),  # Normal scores
        np.random.normal(0.8, 0.1, 100)   # Anomalous scores
    ])
    
    # Calibrate
    result: CalibrationResult = calibrator.calibrate(scores)
    
    print(f"Calibration Results:")
    print(f"  Method: {result.method}")
    print(f"  Threshold: {result.threshold:.4f}")
    print(f"  Score Statistics: {result.score_statistics}")
    
    # Test update_threshold
    for i in range(10):
        new_score: float = np.random.normal(0.3, 0.1)
        threshold: Optional[float] = calibrator.update_threshold(new_score)
        if i % 5 == 0:
            print(f"  Update {i}: score={new_score:.4f}, threshold={threshold}")
    
    # Save state
    output_path: Path = Path("state/threshold_calibration_state.json")
    if calibrator.save_calibration_state(output_path):
        print(f"State saved to {output_path}")
