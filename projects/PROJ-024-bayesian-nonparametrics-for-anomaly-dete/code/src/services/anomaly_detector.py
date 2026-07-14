"""
Anomaly Detector Service with Resource Validation.

Implements the core anomaly detection pipeline with resource constraint validation
(RAM and runtime) as per FR-008.
"""

import os
import sys
import time
import json
import logging
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

import numpy as np

# Import from local project structure (relative to code/src)
# Note: Assuming this file is run as `python -m src.services.anomaly_detector`
# or added to sys.path.
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore
except ImportError:
    # Fallback for direct script execution if package structure isn't set up
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore


logger = logging.getLogger(__name__)

# Resource limits (FR-008)
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 6.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600


@dataclass
class ResourceUsage:
    """Container for resource usage metrics."""
    peak_ram_mb: float
    runtime_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "completed"  # "completed", "failed_ram", "failed_time"
    error_message: Optional[str] = None


class ResourceValidator:
    """
    Validates resource usage against configured limits.
    Measures peak RAM and total runtime.
    """

    def __init__(self, max_ram_gb: float = MAX_RAM_GB, max_runtime_sec: float = MAX_RUNTIME_SECONDS):
        self.max_ram_bytes = max_ram_gb * (1024 ** 3)
        self.max_runtime_seconds = max_runtime_sec
        self._start_time: Optional[float] = None
        self._peak_memory: int = 0
        self._is_tracking = False

    def start_tracking(self) -> None:
        """Start tracking memory and time."""
        tracemalloc.start()
        self._start_time = time.time()
        self._is_tracking = True
        logger.info("Resource tracking started.")

    def stop_tracking(self) -> ResourceUsage:
        """Stop tracking and return usage metrics."""
        if not self._is_tracking:
            raise RuntimeError("Tracking was not started.")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._is_tracking = False

        runtime = time.time() - self._start_time if self._start_time else 0.0
        peak_ram_mb = peak / (1024 * 1024)
        self._peak_memory = peak

        status = "completed"
        error_message = None

        # Check limits
        if peak > self.max_ram_bytes:
            status = "failed_ram"
            error_message = f"Peak RAM {peak_ram_mb:.2f} MB exceeds limit {self.max_ram_bytes / (1024*1024):.2f} MB"
        elif runtime > self.max_runtime_seconds:
            status = "failed_time"
            error_message = f"Runtime {runtime:.2f}s exceeds limit {self.max_runtime_seconds:.2f}s"

        logger.info(f"Resource tracking stopped. Peak RAM: {peak_ram_mb:.2f} MB, Runtime: {runtime:.2f}s, Status: {status}")

        return ResourceUsage(
            peak_ram_mb=peak_ram_mb,
            runtime_seconds=runtime,
            status=status,
            error_message=error_message
        )

    def check_limits(self, peak_ram_mb: float, runtime_seconds: float) -> Tuple[bool, Optional[str]]:
        """
        Check if given metrics exceed limits.
        Returns (is_valid, error_message).
        """
        peak_ram_bytes = peak_ram_mb * 1024 * 1024

        if peak_ram_bytes > self.max_ram_bytes:
            return False, f"Peak RAM {peak_ram_mb:.2f} MB exceeds limit {self.max_ram_bytes / (1024*1024):.2f} MB"

        if runtime_seconds > self.max_runtime_seconds:
            return False, f"Runtime {runtime_seconds:.2f}s exceeds limit {self.max_runtime_seconds:.2f}s"

        return True, None


class AnomalyDetectorService:
    """
    Main service for anomaly detection using DP-GMM.
    Includes resource validation logic.
    """

    def __init__(self, config: Optional[DPGMMConfig] = None, resource_limits: Optional[ResourceValidator] = None):
        self.config = config or DPGMMConfig()
        self.model: Optional[DPGMMModel] = None
        self.resource_validator = resource_limits or ResourceValidator()
        self.results_cache: List[AnomalyScore] = []

    def load_model(self, model_path: str) -> None:
        """Load a pre-trained model from disk."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        # Placeholder for actual loading logic
        logger.info(f"Loading model from {model_path}")
        self.model = DPGMMModel(self.config)
        # In a real implementation, load weights here

    def process_stream(self, data: np.ndarray, anomaly_threshold: float = 0.95) -> List[AnomalyScore]:
        """
        Process a stream of data, detect anomalies, and validate resources.

        Args:
            data: Input time series data (numpy array).
            anomaly_threshold: Threshold for anomaly classification.

        Returns:
            List of AnomalyScore objects.

        Raises:
            RuntimeError: If resource limits are exceeded during processing.
        """
        if not self.resource_validator._is_tracking:
            self.resource_validator.start_tracking()

        try:
            if self.model is None:
                self.model = DPGMMModel(self.config)
                self.model.fit(data)

            scores = []
            for i, point in enumerate(data):
                score = self.compute_score(point, self.model)
                score.is_anomaly = score.score > anomaly_threshold
                scores.append(score)

            # Validate resources at the end of processing
            usage = self.resource_validator.stop_tracking()

            if usage.status != "completed":
                logger.error(f"Resource limit exceeded: {usage.error_message}")
                raise RuntimeError(usage.error_message)

            self.results_cache = scores
            return scores

        except Exception as e:
            # Ensure tracking is stopped even on error
            if self.resource_validator._is_tracking:
                try:
                    self.resource_validator.stop_tracking()
                except Exception:
                    pass
            raise e

    def update_model(self, new_data: np.ndarray) -> None:
        """Update the model with new data."""
        if self.model is None:
            raise RuntimeError("Model not initialized. Call load_model or process_stream first.")
        self.model.partial_fit(new_data)

    def compute_score(self, point: np.ndarray, model: Optional[DPGMMModel] = None) -> AnomalyScore:
        """Compute anomaly score for a single point."""
        if model is None:
            if self.model is None:
                raise RuntimeError("No model available.")
            model = self.model
        score_val = model.score_point(point)
        return AnomalyScore(
            value=float(score_val),
            timestamp=datetime.now(),
            is_anomaly=False,
            component_assignments=None,
            uncertainty=None
        )

    def get_uncertainty(self, scores: List[AnomalyScore]) -> Dict[str, float]:
        """Calculate uncertainty metrics from scores."""
        if not scores:
            return {"mean": 0.0, "std": 0.0, "max": 0.0}
        vals = [s.value for s in scores]
        return {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "max": float(np.max(vals))
        }

    def save_checkpoint(self, path: str, metrics: Optional[Dict[str, Any]] = None) -> None:
        """Save current state and metrics to a checkpoint file."""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else vars(self.config),
            "metrics": metrics or {}
        }
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        logger.info(f"Checkpoint saved to {path}")

    def validate_resources(self, peak_ram_mb: float, runtime_seconds: float) -> bool:
        """
        Explicitly validate resource usage against limits.
        Raises RuntimeError if limits are exceeded.
        """
        is_valid, error_msg = self.resource_validator.check_limits(peak_ram_mb, runtime_seconds)
        if not is_valid:
            raise RuntimeError(f"Resource validation failed: {error_msg}")
        return True


def main():
    """
    Main entry point for resource validation testing.
    Simulates a workload and validates resource limits.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting AnomalyDetectorService Resource Validation Test")

    # Create service
    service = AnomalyDetectorService()

    # Generate synthetic data for testing (small scale to avoid actual timeout/RAM issues in test)
    # In real usage, this would be loaded from data/
    np.random.seed(42)
    test_data = np.random.randn(1000)

    try:
        # Process data
        results = service.process_stream(test_data)
        logger.info(f"Processed {len(results)} points. Detected {sum(1 for r in results if r.is_anomaly)} anomalies.")

        # Save a dummy checkpoint
        service.save_checkpoint("data/processed/results/resource_validation_checkpoint.json", {
            "points_processed": len(results),
            "anomalies_detected": sum(1 for r in results if r.is_anomaly)
        })

        logger.info("Resource validation test completed successfully.")

    except RuntimeError as e:
        logger.error(f"Resource validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()