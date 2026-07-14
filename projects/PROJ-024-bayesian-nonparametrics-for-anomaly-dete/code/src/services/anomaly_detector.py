"""
Anomaly Detector Service implementing streaming anomaly detection with DP-GMM.

This module implements the core anomaly detection service, including
resource monitoring (RAM and runtime) to ensure compliance with
GitHub Actions free-tier constraints (FR-008).
"""

import time
import tracemalloc
import psutil
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
import logging
import json

# Import from local project structure (relative to code/src)
from models.dp_gmm import DPGMMModel, DPGMMConfig
from data.windowing import sliding_window, normalize_window
from data.synthetic_generator import generate_synthetic_timeseries
from evaluation.metrics import EvaluationMetrics

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
class ResourceLimits:
    """Resource constraints for the anomaly detection pipeline."""
    max_ram_gb: float = 7.0
    max_runtime_hours: float = 6.0
    max_runtime_seconds: float = field(init=False)

    def __post_init__(self):
        self.max_runtime_seconds = self.max_runtime_hours * 3600

@dataclass
class ResourceMetrics:
    """Collected resource usage metrics."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    cpu_count: int = 0
    available_ram_gb: float = 0.0
    exceeded_ram_limit: bool = False
    exceeded_runtime_limit: bool = False

class AnomalyDetectorService:
    """
    Service for streaming anomaly detection using DP-GMM.

    This service wraps the DP-GMM model and adds:
    - Sliding window processing
    - Resource monitoring (RAM and runtime)
    - Compliance enforcement with GitHub Actions constraints
    """

    def __init__(
        self,
        config: DPGMMConfig,
        resource_limits: Optional[ResourceLimits] = None,
        window_size: int = 50,
        stride: int = 1
    ):
        """
        Initialize the anomaly detector service.

        Args:
            config: DP-GMM configuration
            resource_limits: Resource constraints (defaults to FR-008 limits)
            window_size: Size of sliding window
            stride: Stride for sliding window
        """
        self.config = config
        self.window_size = window_size
        self.stride = stride
        self.limits = resource_limits or ResourceLimits()
        self.model: Optional[DPGMMModel] = None
        self.metrics: Optional[ResourceMetrics] = None
        self._process = psutil.Process()

        logger.info(f"Initialized AnomalyDetectorService with window_size={window_size}, stride={stride}")
        logger.info(f"Resource limits: RAM={self.limits.max_ram_gb}GB, Runtime={self.limits.max_runtime_hours}h")

    def _start_monitoring(self) -> None:
        """Start memory and time monitoring."""
        tracemalloc.start()
        self._start_time = time.time()
        self._initial_ram = self._process.memory_info().rss / (1024 * 1024)  # MB

    def _stop_monitoring(self) -> ResourceMetrics:
        """Stop monitoring and collect metrics."""
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        end_time = time.time()
        runtime_seconds = end_time - self._start_time

        # Get peak RAM from tracemalloc (more accurate for Python objects)
        peak_ram_mb = peak / (1024 * 1024)

        # Also check system RSS for overall process memory
        current_rss_mb = self._process.memory_info().rss / (1024 * 1024)
        peak_ram_mb = max(peak_ram_mb, current_rss_mb)

        self.metrics = ResourceMetrics(
            peak_ram_mb=peak_ram_mb,
            total_runtime_seconds=runtime_seconds,
            cpu_count=os.cpu_count() or 1,
            available_ram_gb=psutil.virtual_memory().available / (1024 * 1024 * 1024),
            exceeded_ram_limit=peak_ram_mb > (self.limits.max_ram_gb * 1024),
            exceeded_runtime_limit=runtime_seconds > self.limits.max_runtime_seconds
        )

        return self.metrics

    def _validate_resources(self) -> bool:
        """
        Validate that resource usage is within limits.

        Returns:
            True if within limits, False otherwise

        Raises:
            ResourceExceededError: If limits are exceeded
        """
        if not self.metrics:
            logger.warning("No metrics collected yet")
            return True

        valid = True
        if self.metrics.exceeded_ram_limit:
            logger.error(f"RAM limit exceeded: {self.metrics.peak_ram_mb:.2f}MB > {self.limits.max_ram_gb * 1024:.2f}MB")
            valid = False

        if self.metrics.exceeded_runtime_limit:
            logger.error(f"Runtime limit exceeded: {self.metrics.total_runtime_seconds:.2f}s > {self.limits.max_runtime_seconds:.2f}s")
            valid = False

        if not valid:
            raise ResourceExceededError(
                f"Resource limits exceeded. RAM: {self.metrics.peak_ram_mb:.2f}MB, "
                f"Runtime: {self.metrics.total_runtime_seconds:.2f}s"
            )

        logger.info(
            f"Resource validation passed: RAM={self.metrics.peak_ram_mb:.2f}MB, "
            f"Runtime={self.metrics.total_runtime_seconds:.2f}s"
        )
        return True

    def load_model(self, model_path: Optional[str] = None) -> None:
        """
        Load or initialize the DP-GMM model.

        Args:
            model_path: Path to saved model (optional)
        """
        if model_path and Path(model_path).exists():
            logger.info(f"Loading model from {model_path}")
            self.model = DPGMMModel.load(model_path)
        else:
            logger.info("Initializing new DP-GMM model")
            self.model = DPGMMModel(self.config)

    def process_stream(
        self,
        data: List[float],
        ground_truth: Optional[List[bool]] = None
    ) -> Dict[str, Any]:
        """
        Process a time series stream with sliding window anomaly detection.

        Args:
            data: Time series data
            ground_truth: Optional ground truth anomaly labels

        Returns:
            Dictionary with results and metrics
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._start_monitoring()

        try:
            logger.info(f"Processing stream of length {len(data)} with window_size={self.window_size}")

            # Generate sliding windows
            windows = list(sliding_window(data, self.window_size, self.stride))
            logger.info(f"Generated {len(windows)} windows")

            anomaly_scores = []
            alpha_derivatives = []
            weight_variances = []

            for i, window in enumerate(windows):
                # Normalize window
                normalized = normalize_window(window)

                # Compute anomaly score
                score = self.model.compute_anomaly_score(normalized)
                anomaly_scores.append(score)

                # Extract signature metrics
                if hasattr(self.model, 'get_signature'):
                    sig = self.model.get_signature()
                    alpha_derivatives.append(sig.get('alpha_derivative', 0.0))
                    weight_variances.append(sig.get('weight_variance', 0.0))

                # Progress logging
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(windows)} windows")

            # Stop monitoring and validate
            self._stop_monitoring()
            self._validate_resources()

            # Compute evaluation metrics if ground truth available
            eval_metrics = None
            if ground_truth and len(ground_truth) == len(anomaly_scores):
                eval_metrics = self._compute_evaluation_metrics(anomaly_scores, ground_truth)

            return {
                'anomaly_scores': anomaly_scores,
                'alpha_derivatives': alpha_derivatives,
                'weight_variances': weight_variances,
                'resource_metrics': self.metrics,
                'evaluation_metrics': eval_metrics,
                'n_windows': len(windows),
                'success': True
            }

        except ResourceExceededError:
            self._stop_monitoring()
            raise
        except Exception as e:
            self._stop_monitoring()
            logger.error(f"Error processing stream: {str(e)}")
            raise

    def _compute_evaluation_metrics(
        self,
        scores: List[float],
        ground_truth: List[bool]
    ) -> EvaluationMetrics:
        """Compute evaluation metrics against ground truth."""
        # Simple threshold-based evaluation
        threshold = 0.5
        predictions = [s > threshold for s in scores]

        tp = sum(1 for p, g in zip(predictions, ground_truth) if p and g)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p and not g)
        tn = sum(1 for p, g in zip(predictions, ground_truth) if not p and not g)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if not p and g)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            tp=tp,
            fp=fp,
            tn=tn,
            fn=fn
        )

    def save_checkpoint(self, path: str) -> None:
        """Save model checkpoint."""
        if not self.model:
            raise RuntimeError("No model to save")

        self.model.save(path)
        logger.info(f"Model checkpoint saved to {path}")

    def get_resource_report(self) -> Dict[str, Any]:
        """Get a formatted resource usage report."""
        if not self.metrics:
            return {'status': 'no_metrics', 'message': 'No resources measured yet'}

        return {
            'status': 'success' if not (self.metrics.exceeded_ram_limit or self.metrics.exceeded_runtime_limit) else 'exceeded',
            'peak_ram_mb': self.metrics.peak_ram_mb,
            'peak_ram_gb': self.metrics.peak_ram_mb / 1024,
            'total_runtime_seconds': self.metrics.total_runtime_seconds,
            'total_runtime_minutes': self.metrics.total_runtime_seconds / 60,
            'cpu_count': self.metrics.cpu_count,
            'available_ram_gb': self.metrics.available_ram_gb,
            'limits': {
                'max_ram_gb': self.limits.max_ram_gb,
                'max_runtime_hours': self.limits.max_runtime_hours
            },
            'compliance': {
                'ram_compliant': not self.metrics.exceeded_ram_limit,
                'runtime_compliant': not self.metrics.exceeded_runtime_limit,
                'fully_compliant': not (self.metrics.exceeded_ram_limit or self.metrics.exceeded_runtime_limit)
            }
        }


class ResourceExceededError(Exception):
    """Exception raised when resource limits are exceeded."""
    pass


def main():
    """
    Main entry point for resource validation testing.

    This function runs a self-contained test of the anomaly detector
    with resource monitoring to verify FR-008 compliance.
    """
    logger.info("=" * 60)
    logger.info("Resource Validation Test - Anomaly Detector Service")
    logger.info("=" * 60)

    # Configuration
    config = DPGMMConfig(
        n_components_max=10,
        convergence_threshold=0.01,
        max_iterations=100,
        random_seed=42
    )

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
        logger.info("Running anomaly detection with resource monitoring...")
        results = service.process_stream(
            synthetic_data['values'],
            ground_truth=ground_truth
        )

        # Print results
        logger.info("=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        logger.info(f"Windows processed: {results['n_windows']}")
        logger.info(f"Anomaly scores computed: {len(results['anomaly_scores'])}")
        logger.info(f"Alpha derivatives computed: {len(results['alpha_derivatives'])}")

        if results['evaluation_metrics']:
            logger.info(f"F1 Score: {results['evaluation_metrics'].f1_score:.4f}")
            logger.info(f"Precision: {results['evaluation_metrics'].precision:.4f}")
            logger.info(f"Recall: {results['evaluation_metrics'].recall:.4f}")

        # Resource report
        report = service.get_resource_report()
        logger.info("=" * 60)
        logger.info("RESOURCE METRICS")
        logger.info("=" * 60)
        logger.info(f"Peak RAM: {report['peak_ram_mb']:.2f} MB ({report['peak_ram_gb']:.2f} GB)")
        logger.info(f"Total Runtime: {report['total_runtime_seconds']:.2f} seconds ({report['total_runtime_minutes']:.2f} minutes)")
        logger.info(f"CPU Count: {report['cpu_count']}")
        logger.info(f"Available RAM: {report['available_ram_gb']:.2f} GB")
        logger.info(f"RAM Compliant: {report['compliance']['ram_compliant']}")
        logger.info(f"Runtime Compliant: {report['compliance']['runtime_compliant']}")
        logger.info(f"Fully Compliant: {report['compliance']['fully_compliant']}")

        # Save report to file
        report_path = Path('data/processed/results/resource_validation_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Resource report saved to {report_path}")

        if report['compliance']['fully_compliant']:
            logger.info("✓ Resource validation PASSED")
            return 0
        else:
            logger.error("✗ Resource validation FAILED")
            return 1

    except ResourceExceededError as e:
        logger.error(f"Resource limits exceeded: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())