"""
Anomaly Detector Service with Resource Validation (FR-008).

This module implements the core anomaly detection service, including
resource monitoring (RAM, runtime) to ensure compliance with GitHub Actions
free-tier constraints (<=2 CPU, 7GB RAM, 6 hours).
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

# Import from sibling modules based on API surface
# Note: Adjusting imports to match the actual project structure (code/src/...)
try:
    from models.dpgmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore
    from data.windowing import WindowedDataset
    from evaluation.metrics import EvaluationMetrics
except ImportError:
    # Fallback for direct execution from code/src/
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.dpgmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore
    from data.windowing import WindowedDataset
    from evaluation.metrics import EvaluationMetrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ResourceUsage:
    """Container for resource usage metrics."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    cpu_count: int = 1
    exceeded_ram_limit: bool = False
    exceeded_time_limit: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ResourceLimits:
    """Configuration for resource limits (FR-008)."""
    max_ram_mb: float = 6500.0  # Leave headroom from 7GB
    max_runtime_seconds: float = 6 * 3600  # 6 hours
    cpu_cores: int = 2

class AnomalyDetectorService:
    """
    Service for anomaly detection with integrated resource monitoring.

    Implements FR-008: Resource Constraint Validation.
    Measures peak RAM and total runtime, failing the run if limits are exceeded.
    """

    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        limits: Optional[ResourceLimits] = None,
        output_dir: str = "data/processed/results"
    ):
        self.config = config or DPGMMConfig()
        self.limits = limits or ResourceLimits()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model: Optional[DPGMMModel] = None
        self.resource_usage = ResourceUsage()
        self._monitoring_active = False
        self._start_time: Optional[float] = None
        self._peak_ram: float = 0.0

        logger.info(f"AnomalyDetectorService initialized with limits: RAM < {self.limits.max_ram_mb}MB, Time < {self.limits.max_runtime_seconds}s")

    def _start_monitoring(self):
        """Start resource monitoring."""
        if self._monitoring_active:
            return

        tracemalloc.start()
        self._start_time = time.time()
        self._monitoring_active = True
        logger.info("Resource monitoring started.")

    def _stop_monitoring(self):
        """Stop resource monitoring and record metrics."""
        if not self._monitoring_active:
            return

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._monitoring_active = False

        if self._start_time:
            self.resource_usage.total_runtime_seconds = time.time() - self._start_time
            self._start_time = None

        self._peak_ram = peak / (1024 * 1024)  # Convert to MB
        self.resource_usage.peak_ram_mb = self._peak_ram
        self.resource_usage.cpu_count = os.cpu_count() or 1
        self.resource_usage.timestamp = datetime.now().isoformat()

        # Check limits
        self._check_limits()

        logger.info(f"Resource monitoring stopped. Peak RAM: {self.resource_usage.peak_ram_mb:.2f}MB, Runtime: {self.resource_usage.total_runtime_seconds:.2f}s")

    def _check_limits(self):
        """Check if resource limits have been exceeded (FR-008)."""
        self.resource_usage.exceeded_ram_limit = self.resource_usage.peak_ram_mb > self.limits.max_ram_mb
        self.resource_usage.exceeded_time_limit = self.resource_usage.total_runtime_seconds > self.limits.max_runtime_seconds

        if self.resource_usage.exceeded_ram_limit:
            logger.error(f"CRITICAL: RAM limit exceeded! Peak: {self.resource_usage.peak_ram_mb:.2f}MB > Limit: {self.limits.max_ram_mb}MB")
            raise MemoryError(f"Resource limit exceeded: Peak RAM {self.resource_usage.peak_ram_mb:.2f}MB exceeds limit {self.limits.max_ram_mb}MB")

        if self.resource_usage.exceeded_time_limit:
            logger.error(f"CRITICAL: Runtime limit exceeded! Time: {self.resource_usage.total_runtime_seconds:.2f}s > Limit: {self.limits.max_runtime_seconds}s")
            raise TimeoutError(f"Resource limit exceeded: Runtime {self.resource_usage.total_runtime_seconds:.2f}s exceeds limit {self.limits.max_runtime_seconds}s")

    def load_model(self, model_path: str) -> None:
        """Load a pre-trained model from disk."""
        self._start_monitoring()
        try:
            logger.info(f"Loading model from {model_path}")
            # Placeholder for actual model loading logic
            # In a real implementation, this would deserialize the DPGMMModel
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            self.model = DPGMMModel(config=self.config)
            logger.info("Model loaded successfully.")
        finally:
            self._stop_monitoring()

    def process_stream(self, data: np.ndarray, window_size: int = 50, stride: int = 1) -> List[AnomalyScore]:
        """
        Process a time series stream using sliding windows.

        Args:
            data: Input time series data (1D array).
            window_size: Size of the sliding window.
            stride: Stride for sliding window.

        Returns:
            List of AnomalyScore objects for each window.
        """
        self._start_monitoring()
        try:
            logger.info(f"Processing stream with window_size={window_size}, stride={stride}")

            if self.model is None:
                raise RuntimeError("Model not loaded. Call load_model() first.")

            scores = []
            n_points = len(data)

            # Simple sliding window logic
            for start in range(0, n_points - window_size + 1, stride):
                end = start + window_size
                window_data = data[start:end]

                # Normalize window
                window_mean = np.mean(window_data)
                window_std = np.std(window_data)
                if window_std == 0:
                    window_std = 1e-6
                normalized_window = (window_data - window_mean) / window_std

                # Compute anomaly score (placeholder for actual model inference)
                score_value = self.model.compute_anomaly_score(normalized_window)
                score = AnomalyScore(
                    timestamp=start,
                    score=score_value,
                    window_data=window_data.tolist(),
                    normalized_data=normalized_window.tolist()
                )
                scores.append(score)

            logger.info(f"Processed {len(scores)} windows.")
            return scores

        finally:
            self._stop_monitoring()

    def update_model(self, data: np.ndarray) -> None:
        """Update the model with new data (online learning)."""
        self._start_monitoring()
        try:
            logger.info("Updating model with new data.")
            if self.model is None:
                raise RuntimeError("Model not loaded.")
            # Placeholder for actual update logic
            # self.model.partial_fit(data)
            logger.info("Model updated.")
        finally:
            self._stop_monitoring()

    def compute_score(self, data: np.ndarray) -> float:
        """Compute a single anomaly score for a data point or window."""
        self._start_monitoring()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded.")
            score = self.model.compute_anomaly_score(data)
            return float(score)
        finally:
            self._stop_monitoring()

    def get_uncertainty(self, data: np.ndarray) -> Dict[str, Any]:
        """Get uncertainty estimates for a prediction."""
        self._start_monitoring()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded.")
            # Placeholder for uncertainty calculation
            return {
                "variance": float(np.var(data)),
                "std_dev": float(np.std(data)),
                "confidence_interval": [0.0, 1.0]
            }
        finally:
            self._stop_monitoring()

    def save_checkpoint(self, path: str, scores: Optional[List[AnomalyScore]] = None) -> None:
        """Save the current model state and optionally scores to disk."""
        self._start_monitoring()
        try:
            logger.info(f"Saving checkpoint to {path}")
            if self.model is None:
                raise RuntimeError("Model not loaded.")

            checkpoint_data = {
                "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else {},
                "timestamp": datetime.now().isoformat(),
                "resource_usage": {
                    "peak_ram_mb": self.resource_usage.peak_ram_mb,
                    "total_runtime_seconds": self.resource_usage.total_runtime_seconds
                }
            }

            if scores:
                checkpoint_data["scores"] = [
                    {
                        "timestamp": s.timestamp,
                        "score": s.score,
                        "window_size": len(s.window_data) if s.window_data else 0
                    }
                    for s in scores
                ]

            with open(path, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"Checkpoint saved to {path}")
        finally:
            self._stop_monitoring()

    def validate_resource_compliance(self) -> ResourceUsage:
        """
        Validate that the current run has not exceeded resource limits.
        This method should be called periodically or at the end of a run.
        """
        if self._monitoring_active:
            self._stop_monitoring()

        self._check_limits()
        return self.resource_usage

    def generate_resource_report(self, output_path: Optional[str] = None) -> str:
        """Generate a resource validation report."""
        if not output_path:
            output_path = str(self.output_dir / "resource_validation_report.md")

        report_lines = [
            "# Resource Validation Report",
            "",
            f"**Timestamp**: {self.resource_usage.timestamp}",
            f"**Peak RAM**: {self.resource_usage.peak_ram_mb:.2f} MB (Limit: {self.limits.max_ram_mb} MB)",
            f"**Total Runtime**: {self.resource_usage.total_runtime_seconds:.2f} seconds (Limit: {self.limits.max_runtime_seconds} seconds)",
            f"**CPU Cores**: {self.resource_usage.cpu_count}",
            "",
            "## Compliance Status",
            ""
        ]

        if self.resource_usage.exceeded_ram_limit:
            report_lines.append("- **RAM**: ❌ FAILED (Exceeded limit)")
        else:
            report_lines.append("- **RAM**: ✅ PASSED")

        if self.resource_usage.exceeded_time_limit:
            report_lines.append("- **Runtime**: ❌ FAILED (Exceeded limit)")
        else:
            report_lines.append("- **Runtime**: ✅ PASSED")

        report_content = "\n".join(report_lines)

        with open(output_path, 'w') as f:
            f.write(report_content)

        logger.info(f"Resource report saved to {output_path}")
        return report_content

def main():
    """Main entry point for resource validation testing."""
    logger.info("Starting Anomaly Detector Resource Validation Test.")

    # Create service with limits
    service = AnomalyDetectorService(
        limits=ResourceLimits(max_ram_mb=6500.0, max_runtime_seconds=3600) # 1 hour for test
    )

    # Generate synthetic data for testing
    logger.info("Generating synthetic test data...")
    np.random.seed(42)
    test_data = np.random.randn(10000)  # 10k points

    try:
        # Start monitoring
        service._start_monitoring()

        # Simulate processing
        logger.info("Simulating processing...")
        # Use a subset for speed in this test
        subset = test_data[:1000]
        scores = service.process_stream(subset, window_size=50, stride=10)

        # Stop monitoring and check
        service._stop_monitoring()

        # Validate
        usage = service.validate_resource_compliance()

        # Generate report
        report = service.generate_resource_report()
        print(report)

        logger.info("Resource validation test completed successfully.")

    except (MemoryError, TimeoutError) as e:
        logger.error(f"Resource limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()