"""
Anomaly Detector Service implementing streaming anomaly detection with DP-GMM.

This module provides the core service for detecting anomalies in time series data
using a Dirichlet Process Gaussian Mixture Model with sliding window inference.
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import numpy as np

# Import from local models module
from ..models.dp_gmm import DPGMMModel, DPGMMConfig
from ..models.anomaly_score import AnomalyScore
from ..data.windowing import sliding_window, normalize_window

# Configure logging
logger = logging.getLogger(__name__)


class AnomalyDetectorService:
    """
    Service for streaming anomaly detection using DP-GMM.

    This service manages the lifecycle of the anomaly detection model, including
    initialization, streaming inference, model updates, and checkpoint management.
    """

    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        window_size: int = 50,
        stride: int = 1,
        checkpoint_dir: Optional[str] = None
    ):
        """
        Initialize the AnomalyDetectorService.

        Args:
            config: Configuration for the DP-GMM model. If None, uses defaults.
            window_size: Size of the sliding window (default: 50).
            stride: Stride for sliding window (default: 1).
            checkpoint_dir: Directory for saving checkpoints. If None, uses 'data/checkpoints'.
        """
        self.config = config or DPGMMConfig()
        self.window_size = window_size
        self.stride = stride
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("data/checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.model: Optional[DPGMMModel] = None
        self.window_buffer: List[np.ndarray] = []
        self.last_timestamp: float = 0.0
        self.inference_history: List[AnomalyScore] = []

        logger.info(f"AnomalyDetectorService initialized with window_size={window_size}, stride={stride}")
        logger.info(f"Checkpoint directory: {self.checkpoint_dir}")

    def load_model(self, checkpoint_path: str) -> bool:
        """
        Load a previously saved model from checkpoint.

        Args:
            checkpoint_path: Path to the checkpoint file.

        Returns:
            True if loading was successful, False otherwise.
        """
        try:
            path = Path(checkpoint_path)
            if not path.exists():
                logger.error(f"Checkpoint file not found: {checkpoint_path}")
                return False

            self.model = DPGMMModel.load(path)
            logger.info(f"Model loaded successfully from {checkpoint_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model from {checkpoint_path}: {e}")
            return False

    def process_stream(self, data: np.ndarray, timestamps: Optional[np.ndarray] = None) -> List[AnomalyScore]:
        """
        Process a stream of observations and compute anomaly scores.

        Args:
            data: Array of observations (shape: [n_samples, n_features] or [n_samples,]).
            timestamps: Optional array of timestamps. If None, uses sequential indices.

        Returns:
            List of AnomalyScore objects for each window step.
        """
        if self.model is None:
            logger.warning("No model loaded. Initializing with default configuration.")
            self.model = DPGMMModel(self.config)

        # Ensure 2D array
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        n_samples = data.shape[0]
        if timestamps is None:
            timestamps = np.arange(n_samples)

        self.inference_history = []

        # Process in sliding windows
        for start_idx in range(0, n_samples - self.window_size + 1, self.stride):
            end_idx = start_idx + self.window_size
            window_data = data[start_idx:end_idx]
            window_timestamps = timestamps[start_idx:end_idx]

            # Normalize the window
            normalized_window, stats = normalize_window(window_data)

            # Update model with window data
            self.update_model(normalized_window, window_timestamps)

            # Compute anomaly scores for the window
            scores = self.compute_score(normalized_window, window_timestamps)

            # Get uncertainty estimates
            uncertainties = self.get_uncertainty(normalized_window)

            # Create AnomalyScore objects
            for i, (score, unc) in enumerate(zip(scores, uncertainties)):
                timestamp = window_timestamps[i] if i < len(window_timestamps) else self.last_timestamp
                self.last_timestamp = timestamp

                anomaly_score = AnomalyScore(
                    timestamp=float(timestamp),
                    score=float(score),
                    uncertainty=float(unc),
                    component_assignments=None,  # Could be populated from model if needed
                    metadata={
                        "window_start": int(start_idx),
                        "window_end": int(end_idx),
                        "window_stats": stats
                    }
                )
                self.inference_history.append(anomaly_score)

        logger.info(f"Processed {len(self.inference_history)} anomaly scores")
        return self.inference_history

    def update_model(self, data: np.ndarray, timestamps: Optional[np.ndarray] = None) -> None:
        """
        Update the model with new window data.

        Args:
            data: Normalized data for the current window.
            timestamps: Optional timestamps for the window.
        """
        if self.model is None:
            logger.error("Cannot update model: model not initialized")
            return

        try:
            # Fit the model on the current window
            self.model.fit(data)
            logger.debug(f"Model updated with {data.shape[0]} observations")
        except Exception as e:
            logger.error(f"Failed to update model: {e}")
            raise

    def compute_score(
        self,
        data: np.ndarray,
        timestamps: Optional[np.ndarray] = None,
        threshold: Optional[float] = None
    ) -> np.ndarray:
        """
        Compute anomaly scores for the given data.

        Args:
            data: Normalized data to score.
            timestamps: Optional timestamps (used for time-varying alpha if applicable).
            threshold: Optional threshold for anomaly flagging.

        Returns:
            Array of anomaly scores.
        """
        if self.model is None:
            logger.error("Cannot compute scores: model not initialized")
            return np.zeros(data.shape[0])

        try:
            scores = self.model.compute_anomaly_scores(data)
            return np.array(scores)
        except Exception as e:
            logger.error(f"Failed to compute anomaly scores: {e}")
            return np.zeros(data.shape[0])

    def get_uncertainty(self, data: np.ndarray) -> np.ndarray:
        """
        Get uncertainty estimates for the given data.

        Args:
            data: Normalized data to get uncertainty for.

        Returns:
            Array of uncertainty estimates.
        """
        if self.model is None:
            logger.error("Cannot compute uncertainty: model not initialized")
            return np.ones(data.shape[0]) * 0.1  # Default uncertainty

        try:
            # For now, use the variance of the posterior as uncertainty
            # This could be enhanced with bootstrap or MCMC estimates
            uncertainties = self.model.get_uncertainty_estimates(data)
            return np.array(uncertainties)
        except Exception as e:
            logger.warning(f"Failed to compute uncertainty, using default: {e}")
            return np.ones(data.shape[0]) * 0.1

    def save_checkpoint(self, path: Optional[str] = None) -> str:
        """
        Save the current model state to a checkpoint.

        Args:
            path: Optional path to save the checkpoint. If None, uses auto-generated path.

        Returns:
            Path to the saved checkpoint.
        """
        if self.model is None:
            logger.error("Cannot save checkpoint: model not initialized")
            raise ValueError("Model not initialized")

        if path is None:
          timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          path = str(self.checkpoint_dir / f"anomaly_detector_{timestamp}.pkl")

        try:
            self.model.save(Path(path))
            logger.info(f"Model checkpoint saved to {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise

    def get_inference_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of all inference results.

        Returns:
            List of dictionaries containing inference results.
        """
        return [score.to_dict() for score in self.inference_history]

    def reset(self) -> None:
        """
        Reset the service state (clear buffers, reinitialize model).
        """
        self.window_buffer = []
        self.last_timestamp = 0.0
        self.inference_history = []
        if self.model:
            self.model = DPGMMModel(self.config)
        logger.info("AnomalyDetectorService reset")


def main():
    """
    Example usage of AnomalyDetectorService.
    """
    logging.basicConfig(level=logging.INFO)

    # Initialize service
    detector = AnomalyDetectorService(window_size=50, stride=1)

    # Generate synthetic test data
    np.random.seed(42)
    n_samples = 200
    data = np.random.randn(n_samples, 1)

    # Inject an anomaly
    anomaly_start = 100
    anomaly_end = 120
    data[anomaly_start:anomaly_end] += 3.0

    # Process the stream
    scores = detector.process_stream(data)

    # Print results
    print(f"Processed {len(scores)} anomaly scores")
    print(f"Sample scores: {[s.score for s in scores[:5]]}")

    # Save checkpoint
    checkpoint_path = detector.save_checkpoint()
    print(f"Checkpoint saved to: {checkpoint_path}")


if __name__ == "__main__":
    main()