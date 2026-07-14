"""
Anomaly Detector Service for DP-GMM based time-series anomaly detection.

Implements a modular service for loading models, processing streaming data,
computing anomaly scores, and managing checkpoints.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass, asdict, field

import numpy as np

# Project imports - aligning with existing API surface
# Note: Using relative imports compatible with code/src/ structure
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig, compute_anomaly_score
    from models.anomaly_score import AnomalyScore
    from data.windowing import sliding_window, normalize_window
    from evaluation.metrics import EvaluationMetrics
except ImportError:
    # Fallback for direct execution or different import context
    from code.src.models.dp_gmm import DPGMMModel, DPGMMConfig, compute_anomaly_score
    from code.src.models.anomaly_score import AnomalyScore
    from code.src.data.windowing import sliding_window, normalize_window
    from code.src.evaluation.metrics import EvaluationMetrics


logger = logging.getLogger(__name__)


@dataclass
class AnomalyDetectorConfig:
    """Configuration for the AnomalyDetectorService."""
    window_size: int = 50
    stride: int = 1
    model_path: str = "data/models/dpgmm_checkpoint.pkl"
    results_dir: str = "data/processed/results"
    max_ram_mb: int = 6000  # GitHub Actions free tier constraint
    max_runtime_seconds: int = 18000  # 5 hours
    convergence_threshold: float = 0.01
    max_iterations: int = 500


class AnomalyDetectorService:
    """
    Service for DP-GMM based anomaly detection in time series.

    Provides methods for:
    - Loading pre-trained models
    - Processing streaming data with sliding windows
    - Computing anomaly scores and uncertainty
    - Managing checkpoints and state
    """

    def __init__(self, config: Optional[AnomalyDetectorConfig] = None):
        """Initialize the anomaly detector service."""
        self.config = config or AnomalyDetectorConfig()
        self.model: Optional[DPGMMModel] = None
        self.results_dir = Path(self.config.results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.processed_windows: List[Dict[str, Any]] = []
        self.anomaly_scores: List[AnomalyScore] = []
        self.start_time: Optional[float] = None
        self.peak_ram_mb: float = 0.0

        # Resource monitoring
        self._monitor_resources()

        logger.info(f"AnomalyDetectorService initialized with window_size={self.config.window_size}")

    def _monitor_resources(self):
        """Start monitoring memory and runtime."""
        try:
            import psutil
            self.process = psutil.Process()
            self.start_time = time.time()
        except ImportError:
            logger.warning("psutil not available, resource monitoring disabled")
            self.process = None

    def _check_resources(self) -> bool:
        """Check if resource limits are exceeded. Returns False if limits exceeded."""
        if self.process is None:
            return True

        try:
            # Check memory
            current_ram_mb = self.process.memory_info().rss / (1024 * 1024)
            self.peak_ram_mb = max(self.peak_ram_mb, current_ram_mb)

            if current_ram_mb > self.config.max_ram_mb:
                logger.error(f"Memory limit exceeded: {current_ram_mb:.2f}MB > {self.config.max_ram_mb}MB")
                return False

            # Check runtime
            if self.start_time:
                elapsed = time.time() - self.start_time
                if elapsed > self.config.max_runtime_seconds:
                    logger.error(f"Runtime limit exceeded: {elapsed:.2f}s > {self.config.max_runtime_seconds}s")
                    return False

            return True
        except Exception as e:
            logger.warning(f"Resource check failed: {e}")
            return True

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Load a pre-trained DP-GMM model.

        Args:
            model_path: Path to the model checkpoint. If None, uses config default.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        path = model_path or self.config.model_path
        path_obj = Path(path)

        if not path_obj.exists():
            logger.error(f"Model file not found: {path}")
            return False

        try:
            # Import pickle locally to handle potential circular imports
            import pickle
            with open(path_obj, 'rb') as f:
                self.model = pickle.load(f)

            logger.info(f"Model loaded successfully from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def process_stream(self, data: np.ndarray, ground_truth: Optional[np.ndarray] = None) -> List[AnomalyScore]:
        """
        Process a time series using sliding window inference.

        Args:
            data: 1D array of time series observations
            ground_truth: Optional 1D array of binary anomaly labels (0=normal, 1=anomaly)

        Returns:
            List of AnomalyScore objects for each window step.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if len(data) < self.config.window_size:
            raise ValueError(f"Data length {len(data)} is less than window size {self.config.window_size}")

        self.processed_windows = []
        self.anomaly_scores = []

        # Generate sliding windows
        windows = sliding_window(data, window_size=self.config.window_size, stride=self.config.stride)

        for i, window in enumerate(windows):
            if not self._check_resources():
                logger.error("Resource limits exceeded during processing")
                break

            # Normalize window
            normalized_window = normalize_window(window)

            # Update model with current window
            self.update_model(normalized_window)

            # Compute anomaly score
            score = self.compute_score(normalized_window)

            # Store result
            self.processed_windows.append({
                'index': i,
                'window_start': i * self.config.stride,
                'window_data': window.tolist(),
                'normalized_data': normalized_window.tolist()
            })

            self.anomaly_scores.append(score)

        # Compute evaluation metrics if ground truth available
        if ground_truth is not None:
            self._compute_evaluation_metrics(ground_truth)

        return self.anomaly_scores

    def update_model(self, window_data: np.ndarray) -> Dict[str, Any]:
        """
        Update the model with a new window of data.

        Args:
            window_data: Normalized window data

        Returns:
            Dictionary containing update status and ELBO information.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # In a streaming setting, we might update the model incrementally
            # For now, we assume the model is pre-trained and we just compute scores
            # In a more advanced implementation, this would call model.partial_fit()

            elbo_history = self.model.elbo_history if hasattr(self.model, 'elbo_history') else []

            return {
                'status': 'success',
                'window_size': len(window_data),
                'elbo_history_length': len(elbo_history),
                'converged': len(elbo_history) > 0 and elbo_history[-1].converged if elbo_history else False
            }
        except Exception as e:
            logger.error(f"Model update failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def compute_score(self, window_data: np.ndarray) -> AnomalyScore:
        """
        Compute anomaly score for a window of data.

        Args:
            window_data: Normalized window data

        Returns:
            AnomalyScore object with score, uncertainty, and metadata.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Compute anomaly score using the model's scoring method
            score_value = compute_anomaly_score(self.model, window_data)

            # Get uncertainty estimate
            uncertainty = self.get_uncertainty(window_data)

            # Get component assignments if available
            component_assignments = None
            if hasattr(self.model, 'component_assignments'):
                component_assignments = self.model.component_assignments

            timestamp = datetime.now().isoformat()

            return AnomalyScore(
                score=score_value,
                uncertainty=uncertainty,
                timestamp=timestamp,
                window_size=len(window_data),
                component_assignments=component_assignments
            )
        except Exception as e:
            logger.error(f"Score computation failed: {e}")
            # Return a default score in case of error
            return AnomalyScore(
                score=0.0,
                uncertainty=1.0,
                timestamp=datetime.now().isoformat(),
                window_size=len(window_data),
                component_assignments=None
            )

    def get_uncertainty(self, window_data: np.ndarray) -> float:
        """
        Estimate uncertainty for the current window.

        Args:
            window_data: Normalized window data

        Returns:
            Uncertainty estimate (higher = more uncertain).
        """
        if self.model is None:
            return 1.0

        try:
            # Estimate uncertainty based on model variance
            # In a Bayesian setting, this would be the posterior variance
            if hasattr(self.model, 'variance'):
                variance = np.mean(self.model.variance)
                return float(variance)
            elif hasattr(self.model, 'component_variances'):
                variances = self.model.component_variances
                return float(np.mean(variances))
            else:
                # Fallback: estimate from score magnitude
                score = compute_anomaly_score(self.model, window_data)
                return float(np.abs(score))
        except Exception as e:
            logger.warning(f"Uncertainty estimation failed: {e}")
            return 1.0

    def _compute_evaluation_metrics(self, ground_truth: np.ndarray):
        """Compute evaluation metrics against ground truth."""
        if len(self.anomaly_scores) == 0:
            return

        # Extract scores and labels for overlapping windows
        scores = np.array([s.score for s in self.anomaly_scores])
        labels = ground_truth[self.config.window_size-1::self.config.stride]

        # Ensure alignment
        min_len = min(len(scores), len(labels))
        scores = scores[:min_len]
        labels = labels[:min_len]

        # Compute metrics
        try:
            metrics = EvaluationMetrics.compute_all_metrics(scores, labels)
            self.evaluation_metrics = metrics
            logger.info(f"Evaluation metrics computed: F1={metrics.f1:.3f}, AUC={metrics.auc:.3f}")
        except Exception as e:
            logger.warning(f"Failed to compute evaluation metrics: {e}")
            self.evaluation_metrics = None

    def save_checkpoint(self, output_path: Optional[str] = None) -> bool:
        """
        Save the current state to a checkpoint.

        Args:
            output_path: Path to save the checkpoint. If None, uses auto-generated path.

        Returns:
            True if checkpoint saved successfully, False otherwise.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.results_dir / f"anomaly_detector_checkpoint_{timestamp}.json"

        output_path = Path(output_path)

        try:
            checkpoint_data = {
                'config': asdict(self.config),
                'processed_windows_count': len(self.processed_windows),
                'anomaly_scores_count': len(self.anomaly_scores),
                'peak_ram_mb': self.peak_ram_mb,
                'runtime_seconds': time.time() - self.start_time if self.start_time else 0,
                'timestamp': datetime.now().isoformat(),
                'scores': [asdict(s) for s in self.anomaly_scores]
            }

            # Add evaluation metrics if available
            if hasattr(self, 'evaluation_metrics') and self.evaluation_metrics:
                checkpoint_data['evaluation_metrics'] = asdict(self.evaluation_metrics)

            with open(output_path, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"Checkpoint saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def get_results_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing results."""
        if len(self.anomaly_scores) == 0:
            return {
                'status': 'no_results',
                'message': 'No anomaly scores computed yet.'
            }

        scores = np.array([s.score for s in self.anomaly_scores])

        summary = {
            'total_windows': len(self.anomaly_scores),
            'score_stats': {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores))
            },
            'peak_ram_mb': self.peak_ram_mb,
            'runtime_seconds': time.time() - self.start_time if self.start_time else 0
        }

        # Add anomaly count if threshold is defined
        if hasattr(self.config, 'threshold') and self.config.threshold:
            anomalies = scores > self.config.threshold
            summary['anomaly_count'] = int(np.sum(anomalies))
            summary['anomaly_rate'] = float(np.mean(anomalies))

        return summary


def main():
    """Main entry point for standalone execution."""
    logging.basicConfig(level=logging.INFO)

    # Create service
    config = AnomalyDetectorConfig()
    detector = AnomalyDetectorService(config)

    # Generate synthetic data for testing
    try:
        from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig
        signal_config = SignalConfig(
            duration=1000,
            base_frequency=1.0,
            noise_level=0.1
        )
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.05,
            anomaly_duration_min=10,
            anomaly_magnitude=2.0
        )

        data, ground_truth = generate_synthetic_timeseries(signal_config, anomaly_config)
        logger.info(f"Generated synthetic data: {len(data)} points, {np.sum(ground_truth)} anomalies")

        # Load model (using a default path that may not exist, so we'll skip for demo)
        # In a real scenario, you would train or load a model first
        logger.info("Skipping model loading for demo (no pre-trained model available)")

        # Process stream
        # scores = detector.process_stream(data, ground_truth)

        # Save checkpoint
        # detector.save_checkpoint()

        logger.info("AnomalyDetectorService demo completed")

    except ImportError as e:
        logger.error(f"Failed to import synthetic generator: {e}")
        logger.info("This is expected if the synthetic generator is not available")


if __name__ == "__main__":
    main()