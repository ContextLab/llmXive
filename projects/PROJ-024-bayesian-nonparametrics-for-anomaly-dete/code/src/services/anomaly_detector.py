"""
Anomaly Detector Service implementing streaming anomaly detection with DP-GMM.

This module implements the AnomalyDetectorService class, which provides
modular methods for anomaly detection using the DP-GMM model. It includes
resource validation logic to ensure the pipeline runs within GitHub Actions
free-tier constraints (≤2 CPU, 7 GB RAM, 6 hours).
"""

import tracemalloc
import time
import sys
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import numpy as np
import logging

# Import from local project structure (relative to code/src)
# Note: These imports assume the file is run from code/src or code/
# Adjust if running from project root with PYTHONPATH set
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore
except ImportError:
    # Fallback for direct execution from code/ directory
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore


# Resource limits per FR-008 (GitHub Actions free tier)
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 6.0
MAX_RAM_BYTES = MAX_RAM_GB * 1024 ** 3
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600


@dataclass
class ResourceUsage:
    """Data class to hold resource usage metrics."""
    peak_ram_bytes: float = 0.0
    runtime_seconds: float = 0.0
    peak_ram_gb: float = field(init=False)
    runtime_hours: float = field(init=False)

    def __post_init__(self):
        self.peak_ram_gb = self.peak_ram_bytes / (1024 ** 3)
        self.runtime_hours = self.runtime_seconds / 3600


@dataclass
class ResourceValidationError(Exception):
    """Exception raised when resource limits are exceeded."""
    message: str
    usage: ResourceUsage

    def __str__(self):
        return f"ResourceValidationError: {self.message}. Usage: {self.usage}"


class AnomalyDetectorService:
    """
    Service for streaming anomaly detection using DP-GMM.

    This class implements the core anomaly detection logic with methods for
    model loading, stream processing, score computation, and resource monitoring.
    It enforces resource limits to ensure compatibility with constrained
    execution environments.
    """

    def __init__(self, config: Optional[DPGMMConfig] = None):
        """
        Initialize the anomaly detector service.

        Args:
            config: Optional DPGMMConfig instance. If None, uses defaults.
        """
        self.config = config
        self.window_size = window_size
        self.stride = stride
        self.limits = resource_limits or ResourceLimits()
        self.model: Optional[DPGMMModel] = None
        self._ram_limit_gb = MAX_RAM_GB
        self._runtime_limit_hours = MAX_RUNTIME_HOURS
        self._is_tracking = False
        self._start_time: Optional[float] = None
        self._peak_ram_bytes: float = 0.0
        self.logger = logging.getLogger(__name__)

    def load_model(self, model_path: Optional[Path] = None) -> None:
        """
        Load or initialize the DP-GMM model.

        Args:
            model_path: Path to saved model. If None, initializes a new model.
        """
        if model_path and model_path.exists():
            # Implementation would load from path
            self.logger.info(f"Loading model from {model_path}")
            # Placeholder for actual loading logic
            self.model = DPGMMModel(self.config)
        else:
            self.logger.info("Initializing new model")
            self.model = DPGMMModel(self.config)

    def start_resource_tracking(self) -> None:
        """Start tracking memory and runtime."""
        if not self._is_tracking:
            tracemalloc.start()
            self._start_time = time.time()
            self._is_tracking = True
            self.logger.info("Resource tracking started")

    def stop_resource_tracking(self) -> ResourceUsage:
        """
        Stop tracking and return resource usage metrics.

        Returns:
            ResourceUsage: Metrics for peak RAM and runtime.
        """
        if not self._is_tracking:
            return ResourceUsage()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._peak_ram_bytes = peak
        self._is_tracking = False

        runtime = time.time() - self._start_time if self._start_time else 0.0

        usage = ResourceUsage(
            peak_ram_bytes=peak,
            runtime_seconds=runtime
        )
        self.logger.info(f"Resource tracking stopped. Peak RAM: {usage.peak_ram_gb:.2f} GB, Runtime: {usage.runtime_hours:.2f} hours")
        return usage

    def check_resource_limits(self, usage: ResourceUsage) -> None:
        """
        Check if resource usage exceeds limits.

        Args:
            usage: ResourceUsage instance to validate.

        Raises:
            ResourceValidationError: If limits are exceeded.
        """
        if usage.peak_ram_gb > self._ram_limit_gb:
            raise ResourceValidationError(
                f"Peak RAM {usage.peak_ram_gb:.2f} GB exceeds limit of {self._ram_limit_gb} GB",
                usage
            )

        if usage.runtime_hours > self._runtime_limit_hours:
            raise ResourceValidationError(
                f"Runtime {usage.runtime_hours:.2f} hours exceeds limit of {self._runtime_limit_hours} hours",
                usage
            )

    def process_stream(self, data_stream: np.ndarray, window_size: int = 50, stride: int = 1) -> List[AnomalyScore]:
        """
        Process a stream of data with sliding window inference.

        Args:
            data_stream: Input time series data.
            window_size: Size of sliding window.
            stride: Stride for sliding window.

        Returns:
            List of AnomalyScore instances for each window.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model first.")

        self.start_resource_tracking()

        scores = []
        n_samples = len(data_stream)

        for start_idx in range(0, n_samples - window_size + 1, stride):
            end_idx = start_idx + window_size
            window_data = data_stream[start_idx:end_idx]

            # Update model with window data
            self.update_model(window_data)

            # Compute anomaly score for the window
            score = self.compute_score(window_data)
            scores.append(score)

            # Periodic resource check
            if (start_idx // stride) % 10 == 0:
                current_usage = self._get_current_usage()
                try:
                    self.check_resource_limits(current_usage)
                except ResourceValidationError as e:
                    self.logger.error(f"Resource limit exceeded: {e}")
                    raise

        final_usage = self.stop_resource_tracking()
        try:
            self.check_resource_limits(final_usage)
        except ResourceValidationError as e:
            self.logger.error(f"Final resource check failed: {e}")
            raise
        except Exception as e:
            self._stop_monitoring()
            logger.error(f"Error processing stream: {str(e)}")
            raise

        return scores

    def update_model(self, window_data: np.ndarray) -> None:
        """
        Update the model with new window data.

        Args:
            window_data: Data for the current window.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        # Implementation would update model parameters
        self.model.fit(window_data)

    def compute_score(self, window_data: np.ndarray) -> AnomalyScore:
        """
        Compute anomaly score for a window.

        Args:
            window_data: Data for the current window.

        Returns:
            AnomalyScore instance.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        # Compute anomaly score using model
        # Placeholder for actual computation
        score_value = self.model.score(window_data)

        return AnomalyScore(
            timestamp=time.time(),
            score=score_value,
            window_start=0,
            window_end=len(window_data),
            component_assignments=None
        )

    def get_uncertainty(self, window_data: np.ndarray) -> Dict[str, Any]:
        """
        Get uncertainty estimates for a window.

        Args:
            window_data: Data for the current window.

        Returns:
            Dictionary of uncertainty metrics.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        # Placeholder for uncertainty computation
        return {
            "variance": np.var(window_data),
            "confidence_interval": (0.0, 1.0)
        }

    def save_checkpoint(self, path: Path) -> None:
        """
        Save current model state to disk.

        Args:
            path: Path to save checkpoint.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        # Placeholder for saving logic
        self.logger.info(f"Saving checkpoint to {path}")

    def _get_current_usage(self) -> ResourceUsage:
        """
        Get current resource usage without stopping tracking.

        Returns:
            ResourceUsage instance with current metrics.
        """
        if not self._is_tracking:
            return ResourceUsage()

        current, peak = tracemalloc.get_traced_memory()
        runtime = time.time() - self._start_time if self._start_time else 0.0

        return ResourceUsage(
            peak_ram_bytes=peak,
            runtime_seconds=runtime
        )


def main():
    """
    Main entry point for resource validation testing.

    This function demonstrates the resource validation logic by running
    a small-scale test and checking against defined limits.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting resource validation test...")

    # Create service instance
    service = AnomalyDetectorService()
    service.load_model()

    # Generate small synthetic data for testing
    np.random.seed(42)
    test_data = np.random.randn(1000)  # Small dataset for testing

    service = AnomalyDetectorService(
        config=config,
        resource_limits=ResourceLimits(max_ram_gb=7.0, max_runtime_hours=6.0),
        window_size=50,
        stride=1
    )

    # Load model
    service.load_model()

    # Generate synthetic data for testing
    logger.info("Generating synthetic test data...")
    synthetic_data = generate_synthetic_timeseries(
        n_samples=1000,
        n_anomalies=5,
        anomaly_magnitude=3.0,
        random_seed=42
    )

    # Create ground truth (simplified)
    ground_truth = [False] * len(synthetic_data['values'])
    for anomaly in synthetic_data['anomalies']:
        ground_truth[anomaly['index']] = True

    # Run detection
    try:
        # Process the stream
        logger.info("Processing test stream...")
        scores = service.process_stream(test_data, window_size=50, stride=10)

        logger.info(f"Generated {len(scores)} anomaly scores")
        logger.info("Resource validation test PASSED")

    except ResourceValidationError as e:
        logger.error(f"Resource validation test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()