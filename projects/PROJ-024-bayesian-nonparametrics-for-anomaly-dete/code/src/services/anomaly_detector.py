"""
AnomalyDetectorService: Core service for streaming anomaly detection using DP-GMM.
Implements resource validation logic (FR-008) to measure peak RAM and runtime.
"""
import time
import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict, field

# Import from sibling modules based on existing API surface
# Note: The API surface lists `code/models/dp_gmm.py` with `DPGMMModel`, `DPGMMConfig`
# We assume the import path resolves relative to code/src/ or via PYTHONPATH
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig, ClusterAnomalyResult
except ImportError:
    # Fallback for direct execution context if package structure is not fully set
    from code.models.dp_gmm import DPGMMModel, DPGMMConfig, ClusterAnomalyResult

# Resource monitoring imports
try:
    import psutil
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    logging.warning("psutil or resource module not available. Resource validation will be skipped.")

logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    """Data class to hold resource usage metrics."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    limit_exceeded: bool = False
    error_message: Optional[str] = None

@dataclass
class AnomalyDetectionResult:
    """Result of an anomaly detection step."""
    timestamp: float
    anomaly_score: float
    is_anomaly: bool
    uncertainty: Optional[Dict[str, Any]] = None
    resource_metrics: Optional[ResourceMetrics] = None

class ResourceValidator:
    """
    Handles measurement of RAM and runtime, and enforces limits.
    Implements FR-008: Fail run if limits exceeded.
    """
    def __init__(self, max_ram_mb: float = 7000.0, max_runtime_seconds: float = 21600.0):
        """
        Initialize validator with limits.
        Default limits: 7 GB RAM, 6 hours runtime (GitHub Actions free tier).
        """
        self.max_ram_mb = max_ram_mb
        self.max_runtime_seconds = max_runtime_seconds
        self._start_time: Optional[float] = None
        self._peak_ram_bytes: int = 0
        self._process: Optional[Any] = None

        if HAS_RESOURCE:
            self._process = psutil.Process(os.getpid())

    def start_tracking(self):
        """Start tracking runtime and memory."""
        self._start_time = time.time()
        self._peak_ram_bytes = 0
        if self._process:
            # Initial measurement
            mem_info = self._process.memory_info()
            self._peak_ram_bytes = mem_info.rss
            logger.debug(f"Resource tracking started. Initial RAM: {self._peak_ram_bytes / 1024 / 1024:.2f} MB")

    def update_peak_memory(self):
        """Update the recorded peak memory usage."""
        if self._process:
            try:
                current_ram = self._process.memory_info().rss
                if current_ram > self._peak_ram_bytes:
                    self._peak_ram_bytes = current_ram
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        runtime = 0.0
        if self._start_time:
            runtime = time.time() - self._start_time

        peak_ram_mb = self._peak_ram_bytes / (1024 * 1024)

        limit_exceeded = False
        error_msg = None

        if peak_ram_mb > self.max_ram_mb:
            limit_exceeded = True
            error_msg = f"Peak RAM ({peak_ram_mb:.2f} MB) exceeded limit ({self.max_ram_mb:.2f} MB)"
        elif runtime > self.max_runtime_seconds:
            limit_exceeded = True
            error_msg = f"Runtime ({runtime:.2f} s) exceeded limit ({self.max_runtime_seconds:.2f} s)"

        return ResourceMetrics(
            peak_ram_mb=peak_ram_mb,
            total_runtime_seconds=runtime,
            limit_exceeded=limit_exceeded,
            error_message=error_msg
        )

    def check_and_fail(self) -> bool:
        """
        Check if limits are exceeded. If so, log error and raise SystemExit.
        Returns True if limits were exceeded (and process would exit).
        """
        metrics = self.get_current_metrics()
        if metrics.limit_exceeded:
            logger.error(f"RESOURCE LIMIT EXCEEDED: {metrics.error_message}")
            # Write a report to disk before exiting as per FR-008 requirements
            report_path = Path("data/processed/results/resource_validation_report.md")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                f.write(f"# Resource Validation Failure\n\n")
                f.write(f"- Peak RAM: {metrics.peak_ram_mb:.2f} MB (Limit: {self.max_ram_mb:.2f} MB)\n")
                f.write(f"- Runtime: {metrics.total_runtime_seconds:.2f} s (Limit: {self.max_runtime_seconds:.2f} s)\n")
                f.write(f"- Error: {metrics.error_message}\n")
            raise SystemExit(1)
        return False

    def stop(self) -> ResourceMetrics:
        """Stop tracking and return final metrics."""
        metrics = self.get_current_metrics()
        logger.info(f"Resource tracking stopped. Peak RAM: {metrics.peak_ram_mb:.2f} MB, Runtime: {metrics.total_runtime_seconds:.2f} s")
        return metrics

class AnomalyDetectorService:
    """
    Service for streaming anomaly detection using DP-GMM.
    Includes resource validation logic to enforce FR-008.
    """
    def __init__(self, config: DPGMMConfig, max_ram_mb: float = 7000.0, max_runtime_seconds: float = 21600.0):
        self.config = config
        self.model: Optional[DPGMMModel] = None
        self.validator = ResourceValidator(max_ram_mb, max_runtime_seconds)
        self.results: List[AnomalyDetectionResult] = []
        self._initialized = False

    def load_model(self, model_path: Optional[str] = None):
        """Load a pre-trained model or initialize a new one."""
        logger.info("Loading model...")
        self.validator.start_tracking()
        try:
            if model_path and Path(model_path).exists():
                # Implementation of loading logic would go here
                # For now, we assume initialization based on config
                logger.info(f"Loading model from {model_path} (stub)")
            self.model = DPGMMModel(config=self.config)
            self._initialized = True
        finally:
            # Update memory after load
            self.validator.update_peak_memory()

    def process_stream(self, data_stream: List[Dict[str, Any]]) -> List[AnomalyDetectionResult]:
        """
        Process a stream of observations and return anomaly detection results.
        Implements resource validation at the end of processing.
        """
        if not self._initialized or self.model is None:
            raise RuntimeError("Model not initialized. Call load_model() first.")

        self.validator.start_tracking()
        self.results = []

        logger.info(f"Processing stream of {len(data_stream)} observations...")

        for i, obs in enumerate(data_stream):
            # Update memory usage periodically
            if i % 100 == 0:
                self.validator.update_peak_memory()
                self.validator.check_and_fail()

            timestamp = obs.get("timestamp", time.time())
            value = obs.get("value")

            if value is None:
                continue

            # Compute anomaly score
            score, uncertainty = self.compute_score(value, timestamp)
            is_anomaly = score > self.config.threshold

            result = AnomalyDetectionResult(
                timestamp=timestamp,
                anomaly_score=score,
                is_anomaly=is_anomaly,
                uncertainty=uncertainty
            )
            self.results.append(result)

        # Final resource check
        self.validator.update_peak_memory()
        final_metrics = self.validator.stop()

        # Attach final metrics to the last result (or all, depending on requirement)
        if self.results:
            self.results[-1].resource_metrics = final_metrics

        # Enforce limit: if exceeded, the check_and_fail inside the loop or at stop()
        # would have raised SystemExit. If we are here, limits were respected.
        # However, we explicitly check again to ensure no race conditions.
        if final_metrics.limit_exceeded:
            raise RuntimeError(f"Resource limits exceeded during processing: {final_metrics.error_message}")

        return self.results

    def update_model(self, new_data: List[Dict[str, Any]]):
        """Update the model with new data."""
        if self.model is None:
            raise RuntimeError("Model not initialized.")
        self.validator.start_tracking()
        try:
            self.model.update(new_data)
        finally:
            self.validator.update_peak_memory()
            self.validator.check_and_fail()

    def compute_score(self, value: float, timestamp: float) -> Tuple[float, Optional[Dict[str, Any]]]:
        """Compute anomaly score for a single observation."""
        if self.model is None:
            raise RuntimeError("Model not initialized.")
        return self.model.compute_anomaly_score(value, timestamp)

    def get_uncertainty(self) -> Dict[str, Any]:
        """Get uncertainty estimates from the model."""
        if self.model is None:
            raise RuntimeError("Model not initialized.")
        return self.model.get_uncertainty()

    def save_checkpoint(self, path: str):
        """Save the current model state to disk."""
        if self.model is None:
            raise RuntimeError("Model not initialized.")
        self.model.save(path)
        logger.info(f"Model checkpoint saved to {path}")

    def get_resource_report(self) -> Dict[str, Any]:
        """Get the resource validation report."""
        metrics = self.validator.get_current_metrics()
        return asdict(metrics)

def main():
    """
    Main entry point for resource validation testing.
    Runs a simulation to measure RAM and runtime, then validates against limits.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting AnomalyDetectorService Resource Validation (T049)...")

    # Create a simple config
    config = DPGMMConfig(
        max_components=10,
        concentration_prior=1.0,
        threshold=0.5,
        window_size=50
    )

    # Initialize service
    service = AnomalyDetectorService(config, max_ram_mb=7000.0, max_runtime_seconds=21600.0)

    # Load model (initializes internally)
    service.load_model()

    # Generate synthetic data for testing (small subset to avoid long runtime)
    # In a real scenario, this would come from a real dataset
    import numpy as np
    np.random.seed(42)
    synthetic_data = [
        {"timestamp": time.time() + i, "value": np.random.normal(0, 1)}
        for i in range(1000)
    ]

    logger.info("Processing synthetic data stream...")
    try:
        results = service.process_stream(synthetic_data)
        logger.info(f"Processed {len(results)} observations.")
        
        # Get and log final metrics
        report = service.get_resource_report()
        logger.info(f"Resource Report: {report}")
        
        if report["limit_exceeded"]:
            logger.error("Resource limits exceeded!")
            sys.exit(1)
        else:
            logger.info("Resource validation passed.")
            sys.exit(0)
    except SystemExit as e:
        # Re-raise SystemExit to ensure proper exit code propagation
        raise
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()