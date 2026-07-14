"""
Anomaly Detector Service with Resource Validation Logic.

This module implements the core anomaly detection service, including
resource monitoring (RAM and runtime) to ensure compliance with
GitHub Actions free-tier constraints (FR-008).
"""

import os
import sys
import time
import tracemalloc
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
import numpy as np

# Local imports based on project structure
# Note: Imports are relative to code/src/ when run as module, or absolute if PYTHONPATH set
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig, compute_anomaly_score
    from models.anomaly_score import AnomalyScore
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from data.windowing import SlidingWindow
    from evaluation.metrics import EvaluationMetrics
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.anomaly_score import AnomalyScore
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from data.windowing import SlidingWindow
    from evaluation.metrics import EvaluationMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resource limits per FR-008 (GitHub Actions free tier)
MAX_RAM_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB
MAX_RUNTIME_SECONDS = 6 * 3600          # 6 hours

@dataclass
class ResourceMetrics:
    """Container for resource usage metrics."""
    peak_ram_bytes: float = 0.0
    total_runtime_seconds: float = 0.0
    cpu_usage_percent: float = 0.0
    exceeded_ram_limit: bool = False
    exceeded_runtime_limit: bool = False

@dataclass
class ResourceValidationResult:
    """Result of resource validation check."""
    passed: bool
    metrics: ResourceMetrics
    message: str

class ResourceMonitor:
    """Monitors system resource usage during execution."""

    def __init__(self, max_ram_bytes: float = MAX_RAM_BYTES, max_runtime_seconds: float = MAX_RUNTIME_SECONDS):
        self.max_ram_bytes = max_ram_bytes
        self.max_runtime_seconds = max_runtime_seconds
        self.start_time: Optional[float] = None
        self.peak_ram: float = 0.0
        self._monitoring = False

    def start(self):
        """Start monitoring resources."""
        if not self._monitoring:
            tracemalloc.start()
            self.start_time = time.time()
            self._monitoring = True
            logger.info("Resource monitoring started.")

    def stop(self) -> ResourceMetrics:
        """Stop monitoring and return metrics."""
        if not self._monitoring:
            raise RuntimeError("Monitoring not started.")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._monitoring = False

        self.peak_ram = peak
        runtime = time.time() - self.start_time if self.start_time else 0.0

        return ResourceMetrics(
            peak_ram_bytes=peak,
            total_runtime_seconds=runtime,
            exceeded_ram_limit=peak > self.max_ram_bytes,
            exceeded_runtime_limit=runtime > self.max_runtime_seconds
        )

    def get_current_snapshot(self) -> Dict[str, float]:
        """Get a snapshot of current resource usage without stopping."""
        if not self._monitoring:
            return {}

        current, peak = tracemalloc.get_traced_memory()
        runtime = time.time() - self.start_time if self.start_time else 0.0

        return {
            'current_ram_bytes': current,
            'peak_ram_bytes': peak,
            'elapsed_seconds': runtime
        }

class AnomalyDetectorService:
    """
    Main service for anomaly detection using DP-GMM with resource validation.

    This service wraps the model inference pipeline and ensures that
    resource constraints (RAM and runtime) are not exceeded.
    """

    def __init__(
        self,
        model_config: Optional[DPGMMConfig] = None,
        window_size: int = 50,
        stride: int = 1,
        max_ram_bytes: float = MAX_RAM_BYTES,
        max_runtime_seconds: float = MAX_RUNTIME_SECONDS
    ):
        self.model_config = model_config or DPGMMConfig()
        self.window_size = window_size
        self.stride = stride
        self.resource_limits = {
            'max_ram_bytes': max_ram_bytes,
            'max_runtime_seconds': max_runtime_seconds
        }

        self.model: Optional[DPGMMModel] = None
        self.windower = SlidingWindow(window_size=window_size, stride=stride)
        self.monitor = ResourceMonitor(
            max_ram_bytes=max_ram_bytes,
            max_runtime_seconds=max_runtime_seconds
        )

        logger.info(f"AnomalyDetectorService initialized with window_size={window_size}, stride={stride}")

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """Load a pre-trained model from disk or initialize a new one."""
        try:
            if model_path and Path(model_path).exists():
                self.model = DPGMMModel.load(model_path)
                logger.info(f"Model loaded from {model_path}")
            else:
                self.model = DPGMMModel(config=self.model_config)
                logger.info("New model initialized.")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def process_stream(self, data: np.ndarray, ground_truth: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Process a stream of data with resource monitoring.

        Args:
            data: Input time series data (1D or 2D array)
            ground_truth: Optional ground truth anomaly labels

        Returns:
            Dictionary containing predictions, scores, and resource metrics
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self.monitor.start()
        start_time = time.time()

        try:
            # Normalize data
            normalized_data = self._normalize(data)

            # Apply sliding window
            windows = self.windower.transform(normalized_data)

            predictions = []
            scores = []
            uncertainties = []

            for window_idx, window in enumerate(windows):
                # Check resource limits periodically
                if window_idx % 100 == 0:
                    snapshot = self.monitor.get_current_snapshot()
                    if snapshot.get('peak_ram_bytes', 0) > self.resource_limits['max_ram_bytes']:
                        raise MemoryError(
                            f"RAM limit exceeded at window {window_idx}: "
                            f"{snapshot['peak_ram_bytes'] / 1e6:.2f} MB > {self.resource_limits['max_ram_bytes'] / 1e6:.2f} MB"
                        )

                # Run inference on window
                result = self.model.predict(window)
                predictions.append(result['prediction'])
                scores.append(result['score'])
                uncertainties.append(result.get('uncertainty', 0.0))

            # Compute final metrics
            end_time = time.time()
            runtime = end_time - start_time

            metrics = EvaluationMetrics(
                predictions=np.array(predictions),
                scores=np.array(scores),
                ground_truth=ground_truth
            )

            # Stop monitoring and get final metrics
            resource_metrics = self.monitor.stop()

            # Validate resource constraints
            validation_result = self._validate_resources(resource_metrics)

            if not validation_result.passed:
                logger.warning(f"Resource validation failed: {validation_result.message}")
                # Continue but log warning - in strict mode we might raise here

            return {
                'predictions': np.array(predictions),
                'scores': np.array(scores),
                'uncertainties': np.array(uncertainties),
                'metrics': metrics,
                'resource_metrics': resource_metrics,
                'validation_result': validation_result,
                'total_windows': len(windows)
            }

        except Exception as e:
            self.monitor.stop()
            logger.error(f"Error during stream processing: {e}")
            raise

    def update_model(self, new_data: np.ndarray) -> bool:
        """Update the model with new data (online learning)."""
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        self.monitor.start()
        try:
            self.model.partial_fit(new_data)
            self.monitor.stop()
            return True
        except Exception as e:
            self.monitor.stop()
            logger.error(f"Failed to update model: {e}")
            return False

    def compute_score(self, data: np.ndarray) -> float:
        """Compute anomaly score for a single data point or window."""
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        self.monitor.start()
        try:
            score = self.model.compute_anomaly_score(data)
            self.monitor.stop()
            return score
        except Exception as e:
            self.monitor.stop()
            logger.error(f"Failed to compute score: {e}")
            raise

    def get_uncertainty(self, data: np.ndarray) -> float:
        """Get uncertainty estimate for a prediction."""
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        self.monitor.start()
        try:
            uncertainty = self.model.get_uncertainty(data)
            self.monitor.stop()
            return uncertainty
        except Exception as e:
            self.monitor.stop()
            logger.error(f"Failed to compute uncertainty: {e}")
            raise

    def save_checkpoint(self, path: str) -> bool:
        """Save the current model state to disk."""
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        try:
            self.model.save(path)
            logger.info(f"Model checkpoint saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to zero mean and unit variance."""
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)

        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        std[std == 0] = 1  # Avoid division by zero

        return (data - mean) / std

    def _validate_resources(self, metrics: ResourceMetrics) -> ResourceValidationResult:
        """
        Validate that resource usage is within limits.

        Args:
            metrics: Resource metrics from monitoring

        Returns:
            ResourceValidationResult indicating pass/fail and details
        """
        passed = True
        messages = []

        if metrics.exceeded_ram_limit:
            passed = False
            ram_mb = metrics.peak_ram_bytes / 1e6
            limit_mb = self.resource_limits['max_ram_bytes'] / 1e6
            messages.append(f"RAM limit exceeded: {ram_mb:.2f} MB > {limit_mb:.2f} MB")

        if metrics.exceeded_runtime_limit:
            passed = False
            runtime_hrs = metrics.total_runtime_seconds / 3600
            limit_hrs = self.resource_limits['max_runtime_seconds'] / 3600
            messages.append(f"Runtime limit exceeded: {runtime_hrs:.2f} hrs > {limit_hrs:.2f} hrs")

        return ResourceValidationResult(
            passed=passed,
            metrics=metrics,
            message="; ".join(messages) if messages else "All resource limits satisfied"
        )

def main():
    """
    Main entry point for running the anomaly detector with resource validation.

    This function demonstrates the resource validation logic by:
    1. Initializing the service
    2. Generating synthetic data (or loading real data if available)
    3. Running inference with monitoring
    4. Reporting resource usage and validation results
    """
    logger.info("Starting AnomalyDetectorService resource validation demo.")

    # Initialize service
    service = AnomalyDetectorService(
        window_size=50,
        stride=1
    )

    # Load or initialize model
    if not service.load_model():
        logger.error("Failed to initialize model.")
        sys.exit(1)

    # Generate synthetic data for testing (small subset for resource validation)
    # In production, this would load real data
    try:
        from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig

        logger.info("Generating synthetic test data...")
        config = AnomalyConfig(
            n_samples=1000,  # Small subset for validation
            anomaly_probability=0.05
        )
        signal_config = SignalConfig(
            signal_type='sine',
            noise_level=0.1
        )

        data, ground_truth = generate_synthetic_timeseries(
            config=config,
            signal_config=signal_config
        )

        logger.info(f"Generated data shape: {data.shape}")

    except Exception as e:
        logger.warning(f"Could not generate synthetic data: {e}. Using random data for validation.")
        # Fallback to random data if generator fails
        data = np.random.randn(1000)
        ground_truth = None

    # Run processing with resource monitoring
    try:
        logger.info("Running anomaly detection with resource monitoring...")
        result = service.process_stream(data, ground_truth)

        # Report results
        metrics = result['resource_metrics']
        validation = result['validation_result']

        logger.info("=" * 60)
        logger.info("RESOURCE VALIDATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Peak RAM: {metrics.peak_ram_bytes / 1e6:.2f} MB")
        logger.info(f"Total Runtime: {metrics.total_runtime_seconds:.2f} seconds")
        logger.info(f"Windows Processed: {result['total_windows']}")
        logger.info(f"Validation Passed: {validation.passed}")
        logger.info(f"Message: {validation.message}")
        logger.info("=" * 60)

        # Exit with error code if validation failed
        if not validation.passed:
            logger.error("Resource validation FAILED. Exiting with error code 1.")
            sys.exit(1)
        else:
            logger.info("Resource validation PASSED. Exiting successfully.")
            sys.exit(0)

    except MemoryError as e:
        logger.error(f"Memory error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()