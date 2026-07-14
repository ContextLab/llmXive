"""
Anomaly Detector Service with Resource Validation Logic.

This module implements the core anomaly detection service with integrated
resource monitoring to ensure compliance with CPU-only execution constraints
(FR-008): Peak RAM ≤ 7GB, Runtime ≤ 6 hours.
"""

import os
import sys
import time
import tracemalloc
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
import logging

# Ensure we can import from code/src if run as script
if __name__ == "__main__" and "code/src" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.anomaly_score import AnomalyScore
# Import DPGMM components - using relative import for package structure
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig
except ImportError:
    # Fallback for direct script execution
    from code.models.dp_gmm import DPGMMModel, DPGMMConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/anomaly_detector.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ResourceConstraints:
    """Resource constraints for the anomaly detection pipeline."""
    max_ram_gb: float = 7.0  # GitHub Actions free-tier limit
    max_runtime_hours: float = 6.0  # GitHub Actions free-tier limit
    cpu_only: bool = True  # Enforce CPU-only execution


@dataclass
class ResourceMetrics:
    """Resource usage metrics collected during execution."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_compliant: bool = True
    violation_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "peak_ram_mb": self.peak_ram_mb,
            "total_runtime_seconds": self.total_runtime_seconds,
            "total_runtime_hours": self.total_runtime_seconds / 3600,
            "timestamp": self.timestamp,
            "is_compliant": self.is_compliant,
            "violation_reasons": self.violation_reasons
        }


class AnomalyDetectorService:
    """
    Anomaly Detection Service with Resource Validation.

    This service wraps the DPGMM model and provides:
    - Resource monitoring (RAM, runtime)
    - Constraint validation
    - Anomaly detection pipeline orchestration
    """

    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        constraints: Optional[ResourceConstraints] = None,
        model_path: Optional[str] = None
    ):
        """
        Initialize the Anomaly Detector Service.

        Args:
            config: DPGMM configuration parameters
            constraints: Resource constraints (RAM, runtime limits)
            model_path: Path to load a pre-trained model
        """
        self.config = config or DPGMMConfig()
        self.constraints = constraints or ResourceConstraints()
        self.model: Optional[DPGMMModel] = None
        self.metrics = ResourceMetrics()
        self._start_time: Optional[float] = None
        self._is_monitoring = False

        # Initialize model if path provided
        if model_path:
            self.load_model(model_path)

        logger.info(f"AnomalyDetectorService initialized with constraints: "
                   f"max_ram={self.constraints.max_ram_gb}GB, "
                   f"max_runtime={self.constraints.max_runtime_hours}h")

    def _check_gpu_availability(self) -> bool:
        """
        Check if GPU is available and raise error if CPU-only mode is enforced.

        Returns:
            True if GPU is available, False otherwise.

        Raises:
            RuntimeError: If GPU is detected but CPU-only mode is enforced.
        """
        try:
            import torch
            if torch.cuda.is_available():
                if self.constraints.cpu_only:
                    raise RuntimeError(
                        "GPU detected but CPU-only mode is enforced (FR-008). "
                        "Set cpu_only=False in constraints or use CPU-only environment."
                    )
                logger.warning("GPU detected but CPU-only mode enforced. "
                             "Falling back to CPU execution.")
                return True
            return False
        except ImportError:
            logger.info("PyTorch not installed. Assuming CPU-only execution.")
            return False

    def _start_monitoring(self):
        """Start resource monitoring."""
        if self._is_monitoring:
            return

        tracemalloc.start()
        self._start_time = time.time()
        self._is_monitoring = True
        logger.info("Resource monitoring started")

    def _stop_monitoring(self) -> ResourceMetrics:
        """
        Stop resource monitoring and collect metrics.

        Returns:
            ResourceMetrics object with collected data.
        """
        if not self._is_monitoring:
            return self.metrics

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._is_monitoring = False

        end_time = time.time()
        runtime_seconds = end_time - self._start_time if self._start_time else 0

        self.metrics.peak_ram_mb = peak / (1024 * 1024)
        self.metrics.total_runtime_seconds = runtime_seconds
        self.metrics.timestamp = datetime.now().isoformat()

        # Validate against constraints
        self._validate_constraints()

        logger.info(f"Resource monitoring stopped. "
                   f"Peak RAM: {self.metrics.peak_ram_mb:.2f}MB, "
                   f"Runtime: {runtime_seconds:.2f}s")

        return self.metrics

    def _validate_constraints(self):
        """
        Validate resource usage against configured constraints.

        Raises:
            RuntimeError: If resource limits are exceeded.
        """
        self.metrics.is_compliant = True
        self.metrics.violation_reasons = []

        # Check RAM limit
        max_ram_mb = self.constraints.max_ram_gb * 1024
        if self.metrics.peak_ram_mb > max_ram_mb:
            self.metrics.is_compliant = False
            reason = (f"Peak RAM {self.metrics.peak_ram_mb:.2f}MB exceeds "
                     f"limit {max_ram_mb:.2f}MB")
            self.metrics.violation_reasons.append(reason)
            logger.error(reason)

        # Check runtime limit
        max_runtime_seconds = self.constraints.max_runtime_hours * 3600
        if self.metrics.total_runtime_seconds > max_runtime_seconds:
            self.metrics.is_compliant = False
            reason = (f"Runtime {self.metrics.total_runtime_seconds:.2f}s exceeds "
                     f"limit {max_runtime_seconds:.2f}s")
            self.metrics.violation_reasons.append(reason)
            logger.error(reason)

        if not self.metrics.is_compliant:
            raise RuntimeError(
                f"Resource constraints violated:\n" +
                "\n".join([f"  - {r}" for r in self.metrics.violation_reasons])
            )

    def load_model(self, model_path: str) -> None:
        """
        Load a pre-trained DPGMM model.

        Args:
            model_path: Path to the saved model file.

        Raises:
            FileNotFoundError: If model file doesn't exist.
            RuntimeError: If loading fails.
        """
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            self.model = DPGMMModel.load(path)
            logger.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {model_path}: {e}")

    def process_stream(self, data: np.ndarray, anomaly_threshold: float = 0.95) -> List[AnomalyScore]:
        """
        Process a stream of observations through the anomaly detection pipeline.

        Args:
            data_stream: List of observation dictionaries with 'timestamp' and 'value'
            window_size: Size of sliding window for inference
            stride: Stride for sliding window

        Returns:
            List of AnomalyScore objects for each window

        Raises:
            RuntimeError: If resource constraints are violated.
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._start_monitoring()

        try:
            scores: List[AnomalyScore] = []

            # Process in sliding windows
            for i in range(0, len(data_stream) - window_size + 1, stride):
                window_data = data_stream[i:i + window_size]
                window_values = [obs['value'] for obs in window_data]

                # Update model with window data
                self.model.update(window_values)

                # Compute anomaly scores for the window
                window_scores = self.model.compute_anomaly_scores(window_values)

                # Create AnomalyScore objects
                for j, score_val in enumerate(window_scores):
                  timestamp = window_data[j].get('timestamp', datetime.now().isoformat())
                  score_obj = AnomalyScore(
                      timestamp=timestamp,
                      anomaly_score=score_val,
                      component_assignments=None,
                      uncertainty=0.0
                  )
                  scores.append(score_obj)

                # Check constraints periodically
                if len(scores) % 100 == 0:
                    current, _ = tracemalloc.get_traced_memory()
                    if current / (1024 * 1024) > self.constraints.max_ram_gb * 1024:
                        raise RuntimeError("RAM limit exceeded during processing")

            return scores

        finally:
            self._stop_monitoring()

    def update_model(self, new_data: List[float]) -> None:
        """
        Update the model with new data.

        Args:
            new_data: List of new observations

        Raises:
            RuntimeError: If model not loaded or constraints violated.
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._start_monitoring()
        try:
            self.model.update(new_data)
        finally:
            self._stop_monitoring()

    def compute_score(self, observation: Dict[str, Any]) -> AnomalyScore:
        """
        Compute anomaly score for a single observation.

        Args:
            observation: Dictionary with 'timestamp' and 'value'

        Returns:
            AnomalyScore object

        Raises:
            RuntimeError: If model not loaded or constraints violated.
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._start_monitoring()
        try:
            score_val = self.model.compute_anomaly_score(observation['value'])
            return AnomalyScore(
                timestamp=observation.get('timestamp', datetime.now().isoformat()),
                anomaly_score=score_val,
                component_assignments=None,
                uncertainty=0.0
            )
        finally:
            self._stop_monitoring()

    def get_uncertainty(self, observation: Dict[str, Any]) -> Dict[str, float]:
        """
        Get uncertainty estimates for an observation.

        Args:
            observation: Dictionary with 'timestamp' and 'value'

        Returns:
            Dictionary with uncertainty metrics

        Raises:
            RuntimeError: If model not loaded or constraints violated.
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._start_monitoring()
        try:
            # Get component probabilities as uncertainty measure
            probs = self.model.get_component_probabilities(observation['value'])
            return {
                "entropy": -sum(p * (np.log(p) if p > 0 else 0) for p in probs),
                "max_probability": max(probs),
                "component_count": len(probs)
            }
        finally:
            self._stop_monitoring()

    def save_checkpoint(self, output_path: str) -> None:
        """
        Save current model state to checkpoint.

        Args:
            output_path: Path to save the checkpoint

        Raises:
            RuntimeError: If model not loaded or save fails.
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._start_monitoring()
        try:
            self.model.save(Path(output_path))
            logger.info(f"Checkpoint saved to {output_path}")
        finally:
            self._stop_monitoring()

    def get_metrics(self) -> ResourceMetrics:
        """
        Get the latest resource metrics.

        Returns:
            ResourceMetrics object
        """
        return self.metrics

    def generate_resource_report(self, output_path: str) -> None:
        """
        Generate a resource validation report.

        Args:
            output_path: Path to save the report JSON
        """
        report = {
            "service": "AnomalyDetectorService",
            "timestamp": datetime.now().isoformat(),
            "constraints": asdict(self.constraints),
            "metrics": self.metrics.to_dict()
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Resource report saved to {output_path}")


def main():
    """
    Main entry point for resource validation testing.

    This function demonstrates the resource monitoring capabilities
    and validates compliance with FR-008 constraints.
    """
    import numpy as np

    logger.info("Starting AnomalyDetectorService resource validation test")

    # Create service with default constraints
    constraints = ResourceConstraints(
        max_ram_gb=7.0,
        max_runtime_hours=6.0,
        cpu_only=True
    )

    service = AnomalyDetectorService(constraints=constraints)

    # Generate synthetic test data
    np.random.seed(42)
    n_samples = 1000
    test_data = [
        {"timestamp": datetime.now().isoformat(), "value": float(val)}
        for val in np.random.randn(n_samples)
    ]

    try:
        # Process the stream
        logger.info(f"Processing {n_samples} observations...")
        scores = service.process_stream(test_data, window_size=50, stride=10)

        # Generate report
        report_path = "data/processed/results/resource_validation_report.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        service.generate_resource_report(report_path)

        # Print summary
        metrics = service.get_metrics()
        print(f"\nResource Validation Summary:")
        print(f"  Peak RAM: {metrics.peak_ram_mb:.2f}MB")
        print(f"  Total Runtime: {metrics.total_runtime_seconds:.2f}s")
        print(f"  Compliant: {metrics.is_compliant}")
        if not metrics.is_compliant:
            print(f"  Violations: {metrics.violation_reasons}")

        logger.info("Resource validation completed successfully")

    except RuntimeError as e:
        logger.error(f"Resource validation failed: {e}")
        raise



if __name__ == "__main__":
    main()