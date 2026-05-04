"""
ThresholdCalibratorService - Service wrapper for anomaly score threshold calibration.

This service provides adaptive threshold computation for anomaly detection
without requiring labeled data, suitable for real-world streaming deployment.

Interface:
  - __init__(self, config: dict = None)
  - calibrate(self, scores: list[float], labels: list[bool] = None) -> dict
  - validate_threshold(self, scores: list[float], labels: list[bool]) -> dict
  - get_decision_boundary(self) -> dict
  - update_decision_boundary(self, new_threshold: float, method: str = None) -> None
  - compute_expected_bounds(self, scores: list[float]) -> dict

Per plan.md Project Structure specification and T073 requirements.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json

# Import from existing project modules
from ..models.anomaly_score import AnomalyScore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThresholdCalibratorConfig:
    """Configuration for threshold calibration."""
    percentile: float = 95.0  # Default 95th percentile
    min_anomaly_rate: float = 0.01  # Minimum expected anomaly rate
    max_anomaly_rate: float = 0.15  # Maximum expected anomaly rate
    std_multiplier: float = 3.0  # Standard deviation multiplier for bounds
    validation_split: float = 0.2  # Fraction for validation if labels provided
    min_samples: int = 100  # Minimum samples required for calibration
    
@dataclass
class CalibrationResult:
    """Result of threshold calibration."""
    threshold: float
    method: str
    anomaly_rate: float
    confidence: float
    bounds: Dict[str, float]
    timestamp: str
    
@dataclass
class ValidationResult:
    """Result of threshold validation."""
    threshold: float
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    timestamp: str
    
class ThresholdCalibratorService:
    """
    Service wrapper for anomaly score threshold calibration.
    
    Provides adaptive threshold computation for anomaly detection without
    requiring labeled data, suitable for real-world streaming deployment.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the threshold calibrator service.
        
        Args:
            config: Optional configuration dictionary. If None, uses defaults.
        """
        self.config = ThresholdCalibratorConfig(**(config or {}))
        self._decision_boundary: Dict[str, Any] = {
            'threshold': None,
            'method': None,
            'calibrated_at': None,
            'score_distribution': None,
            'anomaly_rate': None
        }
        self._validation_history: List[ValidationResult] = []
        self._calibration_history: List[CalibrationResult] = []
        
        logger.info("ThresholdCalibratorService initialized")
        
    def calibrate(self, scores: List[float], labels: Optional[List[bool]] = None) -> Dict[str, Any]:
        """
        Calibrate threshold using score distribution.
        
        Uses adaptive threshold computation based on percentile of score
        distribution, with optional labeled data for validation.
        
        Args:
            scores: List of anomaly scores to calibrate on
            labels: Optional list of ground truth labels for validation
        
        Returns:
            CalibrationResult dictionary with threshold and metadata
        """
        if not scores:
            raise ValueError("Scores list cannot be empty")
        
        if len(scores) < self.config.min_samples:
            logger.warning(
                f"Only {len(scores)} samples, minimum is {self.config.min_samples}. "
                "Calibration may be unreliable."
            )
        
        scores_array = np.array(scores)
        
        # Compute score distribution statistics
        score_mean = np.mean(scores_array)
        score_std = np.std(scores_array)
        score_min = np.min(scores_array)
        score_max = np.max(scores_array)
        
        # Adaptive threshold using percentile method
        threshold = float(np.percentile(scores_array, self.config.percentile))
        
        # Ensure threshold respects anomaly rate bounds
        anomaly_rate = float(np.mean(scores_array >= threshold))
        if anomaly_rate < self.config.min_anomaly_rate:
            # Lower threshold to increase anomaly rate
            target_rate = self.config.min_anomaly_rate
            threshold = float(np.percentile(scores_array, 100 * (1 - target_rate)))
            anomaly_rate = target_rate
        elif anomaly_rate > self.config.max_anomaly_rate:
            # Raise threshold to decrease anomaly rate
            target_rate = self.config.max_anomaly_rate
            threshold = float(np.percentile(scores_array, 100 * (1 - target_rate)))
            anomaly_rate = target_rate
        
        # Compute confidence based on score distribution
        confidence = self._compute_confidence(scores_array, threshold)
        
        # Compute expected bounds
        bounds = self._compute_bounds_from_distribution(scores_array)
        
        # Create calibration result
        result = CalibrationResult(
            threshold=threshold,
            method="percentile_adaptive",
            anomaly_rate=anomaly_rate,
            confidence=confidence,
            bounds=bounds,
            timestamp=datetime.now().isoformat()
        )
        
        # Update decision boundary
        self._decision_boundary = {
            'threshold': threshold,
            'method': result.method,
            'calibrated_at': result.timestamp,
            'score_distribution': {
                'mean': float(score_mean),
                'std': float(score_std),
                'min': float(score_min),
                'max': float(score_max),
                'percentile_95': float(np.percentile(scores_array, 95)),
                'percentile_99': float(np.percentile(scores_array, 99))
            },
            'anomaly_rate': anomaly_rate,
            'config': {
                'percentile': self.config.percentile,
                'min_anomaly_rate': self.config.min_anomaly_rate,
                'max_anomaly_rate': self.config.max_anomaly_rate
            }
        }
        
        # Store in history
        self._calibration_history.append(result)
        
        logger.info(
            f"Calibration complete: threshold={threshold:.4f}, "
            f"anomaly_rate={anomaly_rate:.2%}, confidence={confidence:.2f}"
        )
        
        # If labels provided, validate the threshold
        if labels is not None:
            validation = self.validate_threshold(scores, labels)
            return {
                'calibration': result.__dict__,
                'validation': validation.__dict__,
                'decision_boundary': self._decision_boundary
            }
        
        return {
            'calibration': result.__dict__,
            'decision_boundary': self._decision_boundary
        }
    
    def validate_threshold(self, scores: List[float], labels: List[bool]) -> Dict[str, Any]:
        """
        Validate threshold against ground truth labels.
        
        Computes precision, recall, F1-score, and confusion matrix metrics
        for the current decision boundary threshold.
        
        Args:
            scores: List of anomaly scores
            labels: List of ground truth labels (True = anomaly)
        
        Returns:
            ValidationResult dictionary with metrics
        """
        if not scores or not labels:
            raise ValueError("Scores and labels lists cannot be empty")
        
        if len(scores) != len(labels):
            raise ValueError("Scores and labels must have the same length")
        
        if self._decision_boundary['threshold'] is None:
            raise ValueError("No threshold has been calibrated. Call calibrate() first.")
        
        threshold = self._decision_boundary['threshold']
        
        # Convert to numpy arrays for computation
        scores_array = np.array(scores)
        labels_array = np.array(labels)
        
        # Predict anomalies based on threshold
        predictions = scores_array >= threshold
        
        # Compute confusion matrix
        tp = int(np.sum((predictions == True) & (labels_array == True)))
        fp = int(np.sum((predictions == True) & (labels_array == False)))
        tn = int(np.sum((predictions == False) & (labels_array == False)))
        fn = int(np.sum((predictions == False) & (labels_array == True)))
        
        # Compute metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        result = ValidationResult(
            threshold=threshold,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            timestamp=datetime.now().isoformat()
        )
        
        # Store in validation history
        self._validation_history.append(result)
        
        logger.info(
            f"Validation complete: precision={precision:.2f}, "
            f"recall={recall:.2f}, F1={f1_score:.2f}"
        )
        
        return result.__dict__
    
    def get_decision_boundary(self) -> Dict[str, Any]:
        """
        Get current decision boundary configuration.
        
        Returns:
            Dictionary containing current threshold and metadata
        """
        return self._decision_boundary.copy()
    
    def update_decision_boundary(self, new_threshold: float, method: Optional[str] = None) -> None:
        """
        Update the decision boundary with a new threshold.
        
        Args:
            new_threshold: New threshold value
            method: Optional method name for tracking
        """
        if new_threshold is None or not isinstance(new_threshold, (int, float)):
            raise ValueError("Threshold must be a numeric value")
        
        self._decision_boundary['threshold'] = float(new_threshold)
        if method:
            self._decision_boundary['method'] = method
        self._decision_boundary['calibrated_at'] = datetime.now().isoformat()
        
        logger.info(f"Decision boundary updated: threshold={new_threshold:.4f}, method={method}")
    
    def compute_expected_bounds(self, scores: List[float]) -> Dict[str, Any]:
        """
        Compute expected bounds for anomaly scores.
        
        Calculates statistical bounds (mean ± k*std) and percentile-based
        bounds for the score distribution.
        
        Args:
            scores: List of anomaly scores
        
        Returns:
            Dictionary containing computed bounds
        """
        if not scores:
            raise ValueError("Scores list cannot be empty")
        
        scores_array = np.array(scores)
        
        # Compute bounds
        score_mean = np.mean(scores_array)
        score_std = np.std(scores_array)
        
        bounds = {
            'mean': float(score_mean),
            'std': float(score_std),
            'lower_bound': float(score_mean - self.config.std_multiplier * score_std),
            'upper_bound': float(score_mean + self.config.std_multiplier * score_std),
            'percentile_5': float(np.percentile(scores_array, 5)),
            'percentile_25': float(np.percentile(scores_array, 25)),
            'percentile_50': float(np.percentile(scores_array, 50)),
            'percentile_75': float(np.percentile(scores_array, 75)),
            'percentile_95': float(np.percentile(scores_array, 95)),
            'percentile_99': float(np.percentile(scores_array, 99)),
            'min': float(np.min(scores_array)),
            'max': float(np.max(scores_array)),
            'config': {
                'std_multiplier': self.config.std_multiplier
            }
        }
        
        return bounds
    
    def _compute_confidence(self, scores: np.ndarray, threshold: float) -> float:
        """
        Compute confidence score for calibration.
        
        Based on score distribution spread and threshold position.
        
        Args:
            scores: Array of anomaly scores
            threshold: Calibrated threshold
        
        Returns:
            Confidence value between 0 and 1
        """
        score_std = np.std(scores)
        score_range = np.max(scores) - np.min(scores)
        
        # Avoid division by zero
        if score_range == 0:
            return 0.5
        
        # Confidence based on threshold position relative to distribution
        threshold_position = (threshold - np.min(scores)) / score_range
        
        # Higher confidence if threshold is well-separated from mean
        mean_distance = abs(threshold - np.mean(scores)) / (score_std + 1e-10)
        
        confidence = min(1.0, max(0.0, mean_distance / 3.0))
        
        # Adjust based on threshold position
        if 0.8 <= threshold_position <= 0.99:
            confidence = min(1.0, confidence + 0.2)
        
        return confidence
    
    def _compute_bounds_from_distribution(self, scores: np.ndarray) -> Dict[str, float]:
        """
        Compute bounds from score distribution.
        
        Args:
            scores: Array of anomaly scores
        
        Returns:
            Dictionary containing bound values
        """
        score_mean = np.mean(scores)
        score_std = np.std(scores)
        
        return {
            'lower': float(score_mean - self.config.std_multiplier * score_std),
            'upper': float(score_mean + self.config.std_multiplier * score_std),
            'mean': float(score_mean),
            'std': float(score_std)
        }
    
    def export_config(self, path: Path) -> None:
        """
        Export current configuration to JSON file.
        
        Args:
            path: Path to save configuration
        """
        config_data = {
            'config': self.config.__dict__,
            'decision_boundary': self._decision_boundary,
            'calibration_count': len(self._calibration_history),
            'validation_count': len(self._validation_history)
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        logger.info(f"Configuration exported to {path}")
    
    def import_config(self, path: Path) -> None:
        """
        Import configuration from JSON file.
        
        Args:
            path: Path to load configuration from
        """
        with open(path, 'r') as f:
            config_data = json.load(f)
        
        # Update config
        self.config = ThresholdCalibratorConfig(**config_data.get('config', {}))
        
        # Restore decision boundary if available
        if 'decision_boundary' in config_data:
            self._decision_boundary = config_data['decision_boundary']
        
        logger.info(f"Configuration imported from {path}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of calibration service state.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'decision_boundary': self._decision_boundary,
            'calibration_history_count': len(self._calibration_history),
            'validation_history_count': len(self._validation_history),
            'config': self.config.__dict__,
            'last_calibration': self._calibration_history[-1].__dict__ if self._calibration_history else None,
            'last_validation': self._validation_history[-1].__dict__ if self._validation_history else None
        }
