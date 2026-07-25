"""
Anomaly Detector Service with Resource Validation.

Implements resource validation logic to measure peak RAM and total runtime,
failing the run if limits are exceeded (FR-008).
"""

import os
import sys
import time
import tracemalloc
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import json

# Import existing model components from the project structure
# Note: Using relative imports where possible, falling back to absolute if run as script
try:
    from models.dpgmm import DPGMMModel, DPGMMConfig
except ImportError:
    try:
        from ..models.dpgmm import DPGMMModel, DPGMMConfig
    except ImportError:
        # Fallback for direct execution in code/src/services/
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from models.dpgmm import DPGMMModel, DPGMMConfig

from data.windowing import WindowConfig, sliding_window_iterator
from data.synthetic_generator import generate_synthetic_timeseries, SyntheticDataset
from evaluation.metrics import EvaluationMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resource limits (GitHub Actions free-tier constraints)
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 6.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

@dataclass
class ResourceUsage:
    """Container for resource usage metrics."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    peak_ram_gb: float = 0.0
    exceeded_ram_limit: bool = False
    exceeded_runtime_limit: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None

@dataclass
class AnomalyDetectorConfig:
    """Configuration for the Anomaly Detector Service."""
    window_size: int = 50
    stride: int = 1
    max_clusters: int = 10
    convergence_threshold: float = 0.01
    max_iterations: int = 500
    random_seed: int = 42
    # Resource limits
    max_ram_gb: float = MAX_RAM_GB
    max_runtime_seconds: float = MAX_RUNTIME_SECONDS

class ResourceValidator:
    """
    Validates that resource usage stays within configured limits.
    Implements FR-008: Resource Constraint Validation.
    """

    def __init__(self, max_ram_gb: float = MAX_RAM_GB, max_runtime_seconds: float = MAX_RUNTIME_SECONDS):
        self.max_ram_bytes = max_ram_gb * 1024 * 1024 * 1024
        self.max_runtime_seconds = max_runtime_seconds
        self.peak_memory_bytes = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        tracemalloc.start()

    def start(self):
        """Start tracking resources."""
        self.start_time = time.time()
        tracemalloc.start()

    def check_current(self) -> ResourceUsage:
        """Check current resource usage without stopping tracking."""
        current, peak = tracemalloc.get_traced_memory()
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.peak_memory_bytes = max(self.peak_memory_bytes, peak)

        return ResourceUsage(
            peak_ram_mb=self.peak_memory_bytes / (1024 * 1024),
            peak_ram_gb=self.peak_memory_bytes / (1024 * 1024 * 1024),
            total_runtime_seconds=elapsed,
            exceeded_ram_limit=self.peak_memory_bytes > self.max_ram_bytes,
            exceeded_runtime_limit=elapsed > self.max_runtime_seconds,
            start_time=self.start_time,
            end_time=time.time()
        )

    def stop(self) -> ResourceUsage:
        """Stop tracking and return final usage."""
        self.end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        self.peak_memory_bytes = max(self.peak_memory_bytes, peak)
        tracemalloc.stop()

        elapsed = self.end_time - self.start_time if self.start_time else 0

        usage = ResourceUsage(
            peak_ram_mb=self.peak_memory_bytes / (1024 * 1024),
            peak_ram_gb=self.peak_memory_bytes / (1024 * 1024 * 1024),
            total_runtime_seconds=elapsed,
            exceeded_ram_limit=self.peak_memory_bytes > self.max_ram_bytes,
            exceeded_runtime_limit=elapsed > self.max_runtime_seconds,
            start_time=self.start_time,
            end_time=self.end_time
        )

        return usage

    def validate(self, usage: ResourceUsage) -> bool:
        """
        Validate that usage is within limits.
        Raises RuntimeError if limits are exceeded.
        """
        if usage.exceeded_ram_limit:
            raise RuntimeError(
                f"RAM limit exceeded: {usage.peak_ram_gb:.2f} GB > {self.max_ram_bytes / (1024**3):.2f} GB"
            )
        if usage.exceeded_runtime_limit:
            raise RuntimeError(
                f"Runtime limit exceeded: {usage.total_runtime_seconds:.1f} seconds > {self.max_runtime_seconds} seconds"
            )
        return True

class AnomalyDetectorService:
    """
    Main service for anomaly detection with resource validation.
    Implements modular methods for processing streams, updating models,
    and computing scores while monitoring resource usage.
    """

    def __init__(self, config: Optional[AnomalyDetectorConfig] = None):
        self.config = config or AnomalyDetectorConfig()
        self.model: Optional[DPGMMModel] = None
        self.validator = ResourceValidator(
            max_ram_gb=self.config.max_ram_gb,
            max_runtime_seconds=self.config.max_runtime_seconds
        )
        self.results: List[Dict[str, Any]] = []

    def load_model(self, model_path: str) -> None:
        """Load a pre-trained model from disk."""
        logger.info(f"Loading model from {model_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        # Implementation would load the model
        # For now, we initialize a new one
        self.model = DPGMMModel(config=DPGMMConfig(
            max_clusters=self.config.max_clusters,
            random_seed=self.config.random_seed
        ))

    def process_stream(self, data: List[float], anomaly_timestamps: Optional[List[int]] = None) -> ResourceUsage:
        """
        Process a time series stream with sliding window inference.
        Measures resource usage and fails if limits are exceeded.
        """
        logger.info(f"Processing stream of length {len(data)}")
        self.validator.start()

        try:
            # Initialize windowing
            window_config = WindowConfig(
                window_size=self.config.window_size,
                stride=self.config.stride
            )

            # Process windows
            windows = list(sliding_window_iterator(data, window_config))
            logger.info(f"Extracted {len(windows)} windows")

            # Initialize model if not loaded
            if self.model is None:
                self.model = DPGMMModel(config=DPGMMConfig(
                    max_clusters=self.config.max_clusters,
                    random_seed=self.config.random_seed
                ))

            # Process each window
            for i, window_data in enumerate(windows):
                # Check resources periodically
                if i % 100 == 0:
                    usage = self.validator.check_current()
                    if usage.exceeded_ram_limit or usage.exceeded_runtime_limit:
                        self.validator.stop()
                        raise RuntimeError(f"Resource limit exceeded at window {i}")

                # Train/Update model on window
                self.model.fit(window_data)

                # Compute anomaly scores
                scores = self.model.compute_anomaly_scores(window_data)

                # Store results
                self.results.append({
                    'window_index': i,
                    'mean_score': float(scores.mean()),
                    'max_score': float(scores.max()),
                    'std_score': float(scores.std())
                })

            # Final resource check
            usage = self.validator.stop()
            self.validator.validate(usage)

            logger.info(f"Processing complete. Peak RAM: {usage.peak_ram_mb:.1f} MB, "
                        f"Runtime: {usage.total_runtime_seconds:.1f} seconds")

            return usage

        except Exception as e:
            self.validator.stop()
            logger.error(f"Processing failed: {str(e)}")
            raise

    def update_model(self, new_data: List[float]) -> None:
        """Update the model with new data points."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model first.")
        self.model.update(new_data)

    def compute_score(self, data: List[float]) -> Dict[str, float]:
        """Compute anomaly score for a given data window."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model first.")
        scores = self.model.compute_anomaly_scores(data)
        return {
            'mean': float(scores.mean()),
            'max': float(scores.max()),
            'std': float(scores.std())
        }

    def get_uncertainty(self, data: List[float]) -> Dict[str, float]:
        """Get uncertainty estimates for anomaly scores."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model first.")
        # Placeholder for uncertainty estimation
        return {
            'confidence_interval_95': [0.0, 1.0],
            'variance': 0.1
        }

    def save_checkpoint(self, path: str) -> None:
        """Save current state to a checkpoint file."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model first.")
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        self.model.save(path)
        logger.info(f"Checkpoint saved to {path}")

    def generate_resource_report(self, output_path: str) -> None:
        """Generate a resource validation report."""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        report = {
            'config': {
                'max_ram_gb': self.config.max_ram_gb,
                'max_runtime_seconds': self.config.max_runtime_seconds
            },
            'usage': {
                'peak_ram_mb': self.validator.peak_memory_bytes / (1024 * 1024),
                'peak_ram_gb': self.validator.peak_memory_bytes / (1024 * 1024 * 1024),
                'total_runtime_seconds': 0,  # Will be updated after processing
                'exceeded_ram_limit': False,
                'exceeded_runtime_limit': False
            },
            'status': 'pending'
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Resource report saved to {output_path}")


def main():
    """
    Main entry point for resource validation testing.
    Generates synthetic data, processes it, and validates resource usage.
    """
    logger.info("=" * 80)
    logger.info("Resource Validation Test (T049)")
    logger.info("=" * 80)

    # Configuration
    config = AnomalyDetectorConfig(
        window_size=50,
        stride=1,
        max_clusters=5,
        max_ram_gb=MAX_RAM_GB,
        max_runtime_seconds=MAX_RUNTIME_SECONDS
    )

    # Generate synthetic data for testing
    logger.info("Generating synthetic dataset...")
    dataset = generate_synthetic_timeseries(
        length=1000,
        anomaly_rate=0.1,
        seed=config.random_seed
    )
    data = dataset.signal
    anomaly_timestamps = dataset.anomaly_timestamps

    logger.info(f"Generated {len(data)} data points with {len(anomaly_timestamps)} anomalies")

    # Initialize service
    service = AnomalyDetectorService(config=config)

    # Process stream with resource validation
    try:
        usage = service.process_stream(data, anomaly_timestamps)
        
        # Generate report
        report_path = "data/processed/results/resource_validation_report.json"
        service.generate_resource_report(report_path)
        
        # Update report with actual usage
        import json
        with open(report_path, 'r') as f:
            report = json.load(f)
        report['usage'] = {
            'peak_ram_mb': usage.peak_ram_mb,
            'peak_ram_gb': usage.peak_ram_gb,
            'total_runtime_seconds': usage.total_runtime_seconds,
            'exceeded_ram_limit': usage.exceeded_ram_limit,
            'exceeded_runtime_limit': usage.exceeded_runtime_limit
        }
        report['status'] = 'PASSED' if not (usage.exceeded_ram_limit or usage.exceeded_runtime_limit) else 'FAILED'
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info("=" * 80)
        logger.info("RESOURCE VALIDATION: PASSED")
        logger.info(f"Peak RAM: {usage.peak_ram_mb:.1f} MB ({usage.peak_ram_gb:.2f} GB)")
        logger.info(f"Total Runtime: {usage.total_runtime_seconds:.1f} seconds")
        logger.info(f"Report saved to: {report_path}")
        logger.info("=" * 80)
        
        return 0

    except RuntimeError as e:
        logger.error("=" * 80)
        logger.error("RESOURCE VALIDATION: FAILED")
        logger.error(f"Error: {str(e)}")
        logger.info("=" * 80)
        return 1

    except Exception as e:
        logger.error("=" * 80)
        logger.error("PROCESSING FAILED")
        logger.error(f"Error: {str(e)}")
        logger.info("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())