"""
Anomaly Detector Service with Resource Validation Logic.

This module implements the core anomaly detection service, including:
- Model loading and saving
- Streaming data processing
- Anomaly score computation
- Uncertainty estimation
- Resource validation (RAM and runtime limits)

Resource validation enforces FR-008: The pipeline must fail if peak RAM > 7 GB
or runtime > 6 hours on GitHub Actions free-tier.
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

# Import from sibling modules using the API surface provided
# Note: The API surface lists `code/models/dp_gmm` but T063 moved files to `code/src/`.
# We use relative imports to respect the package structure.
try:
    from ..models.dp_gmm import DPGMMModel, DPGMMConfig
    from ..models.anomaly_score import AnomalyScore
except ImportError:
    # Fallback for direct execution or different import context
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resource limits per FR-008 (GitHub Actions free-tier)
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 6.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600
MAX_RAM_BYTES = MAX_RAM_GB * 1024 * 1024 * 1024

@dataclass
class ResourceUsage:
    """Container for resource usage metrics."""
    peak_ram_bytes: float = 0.0
    peak_ram_gb: float = 0.0
    total_runtime_seconds: float = 0.0
    total_runtime_hours: float = 0.0
    exceeded_ram_limit: bool = False
    exceeded_runtime_limit: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'peak_ram_bytes': self.peak_ram_bytes,
            'peak_ram_gb': self.peak_ram_gb,
            'total_runtime_seconds': self.total_runtime_seconds,
            'total_runtime_hours': self.total_runtime_hours,
            'exceeded_ram_limit': self.exceeded_ram_limit,
            'exceeded_runtime_limit': self.exceeded_runtime_limit,
            'timestamp': self.timestamp
        }

class ResourceValidationError(Exception):
    """Raised when resource limits are exceeded."""
    pass

class AnomalyDetectorService:
    """
    Service for anomaly detection using DP-GMM with resource validation.

    This service wraps the DPGMMModel and adds:
    - Streaming processing capabilities
    - Resource usage monitoring (RAM and runtime)
    - Automatic failure if limits are exceeded
    """

    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        resource_monitor: bool = True,
        report_path: Optional[str] = None
    ):
        """
        Initialize the AnomalyDetectorService.

        Args:
            config: DPGMMConfig for model initialization. If None, uses defaults.
            resource_monitor: Whether to enable RAM and runtime monitoring.
            report_path: Path to write resource usage report.
        """
        self.config = config or DPGMMConfig()
        self.model: Optional[DPGMMModel] = None
        self.resource_monitor = resource_monitor
        self.report_path = Path(report_path) if report_path else None

        # Resource tracking
        self.start_time: Optional[float] = None
        self.peak_ram_bytes: float = 0.0
        self.is_monitoring = False

        if self.resource_monitor:
            logger.info("Resource monitoring enabled. Limits: RAM=%.2f GB, Runtime=%.2f hours",
                      MAX_RAM_GB, MAX_RUNTIME_HOURS)

    def _start_monitoring(self) -> None:
        """Start memory and runtime monitoring."""
        if not self.resource_monitor:
            return

        self.start_time = time.time()
        tracemalloc.start()
        self.is_monitoring = True
        logger.debug("Monitoring started at %s", datetime.fromtimestamp(self.start_time).isoformat())

    def _stop_monitoring(self) -> ResourceUsage:
        """Stop monitoring and return usage metrics."""
        if not self.resource_monitor:
            return ResourceUsage()

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.is_monitoring = False

        runtime_seconds = end_time - self.start_time if self.start_time else 0.0
        peak_ram_gb = peak / (1024 ** 3)

        exceeded_ram = peak > MAX_RAM_BYTES
        exceeded_runtime = runtime_seconds > MAX_RUNTIME_SECONDS

        self.peak_ram_bytes = float(peak)

        usage = ResourceUsage(
            peak_ram_bytes=float(peak),
            peak_ram_gb=peak_ram_gb,
            total_runtime_seconds=runtime_seconds,
            total_runtime_hours=runtime_seconds / 3600,
            exceeded_ram_limit=exceeded_ram,
            exceeded_runtime_limit=exceeded_runtime
        )

        logger.info("Resource Usage: RAM=%.2f GB (limit=%.2f GB), Runtime=%.2f hours (limit=%.2f hours)",
                  peak_ram_gb, MAX_RAM_GB, runtime_seconds / 3600, MAX_RUNTIME_HOURS)

        if exceeded_ram or exceeded_runtime:
            logger.error("Resource limits exceeded!")
            if exceeded_ram:
                logger.error("  - Peak RAM (%.2f GB) exceeded limit (%.2f GB)",
                           peak_ram_gb, MAX_RAM_GB)
            if exceeded_runtime:
                logger.error("  - Runtime (%.2f hours) exceeded limit (%.2f hours)",
                           runtime_seconds / 3600, MAX_RUNTIME_HOURS)

        return usage

    def _check_resource_limits(self, usage: ResourceUsage) -> None:
        """
        Check if resource limits have been exceeded and raise if so.

        Args:
            usage: ResourceUsage object containing measured metrics.

        Raises:
            ResourceValidationError: If RAM or runtime limits are exceeded.
        """
        if usage.exceeded_ram_limit or usage.exceeded_runtime_limit:
            error_msg = "Resource limits exceeded. "
            if usage.exceeded_ram_limit:
                error_msg += f"Peak RAM: {usage.peak_ram_gb:.2f} GB (limit: {MAX_RAM_GB} GB). "
            if usage.exceeded_runtime_limit:
                error_msg += f"Runtime: {usage.total_runtime_hours:.2f} hours (limit: {MAX_RUNTIME_HOURS} hours). "
            error_msg += "Run aborted per FR-008."
            raise ResourceValidationError(error_msg)

    def _save_resource_report(self, usage: ResourceUsage) -> None:
        """Save resource usage report to disk."""
        if not self.report_path:
            return

        self.report_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            'service': 'AnomalyDetectorService',
            'config': self.config.to_dict() if hasattr(self.config, 'to_dict') else str(self.config),
            'resource_usage': usage.to_dict(),
            'limits': {
                'max_ram_gb': MAX_RAM_GB,
                'max_runtime_hours': MAX_RUNTIME_HOURS
            },
            'status': 'PASSED' if not (usage.exceeded_ram_limit or usage.exceeded_runtime_limit) else 'FAILED'
        }

        with open(self.report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info("Resource report saved to: %s", self.report_path)

    def load_model(self, model_path: str) -> None:
        """
        Load a pre-trained DP-GMM model.

        Args:
            model_path: Path to the saved model file.
        """
        logger.info("Loading model from: %s", model_path)
        self.model = DPGMMModel.load(model_path)
        logger.info("Model loaded successfully.")

    def save_checkpoint(self, checkpoint_path: str) -> None:
        """
        Save the current model state to a checkpoint.

        Args:
            checkpoint_path: Path to save the checkpoint.
        """
        if self.model is None:
            raise ValueError("No model loaded. Cannot save checkpoint.")

        logger.info("Saving checkpoint to: %s", checkpoint_path)
        self.model.save(checkpoint_path)
        logger.info("Checkpoint saved successfully.")

    def process_stream(
        self,
        data_stream: np.ndarray,
        window_size: int = 50,
        stride: int = 1,
        return_scores: bool = True
    ) -> Dict[str, Any]:
        """
        Process a stream of data using sliding window inference.

        Args:
            data_stream: 1D numpy array of time series data.
            window_size: Size of the sliding window.
            stride: Stride for the sliding window.
            return_scores: Whether to return anomaly scores.

        Returns:
            Dictionary containing processing results and resource usage.
        """
        self._start_monitoring()

        try:
            logger.info("Processing stream of length %d with window_size=%d, stride=%d",
                      len(data_stream), window_size, stride)

            if self.model is None:
                # Initialize model if not loaded
                self.model = DPGMMModel(self.config)

            # Sliding window processing
            scores = []
            timestamps = []
            windows_processed = 0

            for i in range(0, len(data_stream) - window_size + 1, stride):
                window = data_stream[i:i + window_size]

                # Check resource limits periodically (every 100 windows)
                if windows_processed % 100 == 0 and windows_processed > 0:
                    usage = self._stop_monitoring()
                    self._check_resource_limits(usage)
                    self._start_monitoring()  # Restart monitoring

                # Update model and compute score
                self.model.update_model(window)
                score = self.model.compute_anomaly_score(window)

                if return_scores:
                    scores.append(score)
                timestamps.append(i)
                windows_processed += 1

                # Log progress
                if windows_processed % 1000 == 0:
                    logger.info("Processed %d windows...", windows_processed)

            # Final resource check
            usage = self._stop_monitoring()
            self._check_resource_limits(usage)

            # Save report if path provided
            if self.report_path:
                self._save_resource_report(usage)

            result = {
                'windows_processed': windows_processed,
                'resource_usage': usage.to_dict(),
                'status': 'SUCCESS'
            }

            if return_scores:
                result['scores'] = np.array(scores)
                result['timestamps'] = np.array(timestamps)

            logger.info("Stream processing completed. Windows: %d, Peak RAM: %.2f GB",
                      windows_processed, usage.peak_ram_gb)

            return result

        except ResourceValidationError:
            logger.error("Resource limit exceeded during stream processing. Aborting.")
            self._stop_monitoring()  # Ensure cleanup
            raise
        except Exception as e:
            logger.error("Error during stream processing: %s", str(e))
            self._stop_monitoring()
            raise

    def update_model(self, window: np.ndarray) -> None:
        """
        Update the model with a new window of data.

        Args:
            window: 1D numpy array representing the current window.
        """
        if self.model is None:
            self.model = DPGMMModel(self.config)
        self.model.update_model(window)

    def compute_score(self, window: np.ndarray) -> float:
        """
        Compute anomaly score for a single window.

        Args:
            window: 1D numpy array representing the window.

        Returns:
            Anomaly score as a float.
        """
        if self.model is None:
            self.model = DPGMMModel(self.config)
        return self.model.compute_anomaly_score(window)

    def get_uncertainty(self, window: np.ndarray) -> Dict[str, float]:
        """
        Get uncertainty estimates for a window.

        Args:
            window: 1D numpy array representing the window.

        Returns:
            Dictionary containing uncertainty metrics.
        """
        if self.model is None:
            self.model = DPGMMModel(self.config)
        return self.model.get_uncertainty(window)

    def run_full_pipeline(
        self,
        data_path: str,
        output_path: str,
        window_size: int = 50,
        stride: int = 1
    ) -> Dict[str, Any]:
        """
        Run the full anomaly detection pipeline on a dataset.

        This method:
        1. Loads data from the specified path
        2. Processes the data with sliding window inference
        3. Validates resource usage against limits
        4. Saves results to the output path

        Args:
            data_path: Path to the input data file.
            output_path: Path to save the results.
            window_size: Size of the sliding window.
            stride: Stride for the sliding window.

        Returns:
            Dictionary containing pipeline results and resource usage.
        """
        logger.info("Starting full pipeline. Input: %s, Output: %s", data_path, output_path)

        # Load data
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")

        data = np.loadtxt(data_path, delimiter=',')
        logger.info("Loaded data with shape: %s", data.shape)

        # Process stream
        results = self.process_stream(
            data,
            window_size=window_size,
            stride=stride,
            return_scores=True
        )

        # Save results
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save scores
        scores_path = str(Path(output_path).with_suffix('.scores.csv'))
        np.savetxt(scores_path, results['scores'], delimiter=',', header='anomaly_score')

        # Save metadata
        metadata = {
            'input_file': data_path,
            'output_file': output_path,
            'window_size': window_size,
            'stride': stride,
            'total_windows': results['windows_processed'],
            'resource_usage': results['resource_usage'],
            'timestamp': datetime.now().isoformat()
        }

        metadata_path = str(Path(output_path).with_suffix('.json'))
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info("Pipeline completed successfully. Results saved to: %s", output_path)
        return results


def main():
    """
    Main entry point for resource validation demonstration.

    This function:
    1. Generates synthetic data (small scale for testing)
    2. Runs the anomaly detector with resource monitoring
    3. Validates that resource limits are enforced
    4. Outputs resource usage report
    """
    import argparse

    parser = argparse.ArgumentParser(description='Anomaly Detector Resource Validation')
    parser.add_argument('--data', type=str, default='data/processed/results/synthetic_test.csv',
                      help='Path to input data file')
    parser.add_argument('--output', type=str, default='data/processed/results/resource_validation.json',
                      help='Path to output results')
    parser.add_argument('--window-size', type=int, default=50, help='Window size')
    parser.add_argument('--stride', type=int, default=1, help='Stride')
    parser.add_argument('--no-monitor', action='store_true', help='Disable resource monitoring')
    args = parser.parse_args()

    # Generate synthetic data if not exists (for testing)
    data_path = Path(args.data)
    if not data_path.exists():
        logger.info("Generating synthetic test data...")
        data_path.parent.mkdir(parents=True, exist_ok=True)
        np.random.seed(42)
        synthetic_data = np.random.randn(1000)  # Small dataset for testing
        np.savetxt(data_path, synthetic_data, delimiter=',')
        logger.info("Synthetic data saved to: %s", data_path)

    # Initialize service
    service = AnomalyDetectorService(
        resource_monitor=not args.no_monitor,
        report_path=args.output
    )

    try:
        # Run pipeline
        results = service.run_full_pipeline(
            data_path=str(data_path),
            output_path=args.output,
            window_size=args.window_size,
            stride=args.stride
        )

        print("\n" + "="*60)
        print("Resource Validation Report")
        print("="*60)
        print(f"Status: {results['status']}")
        print(f"Windows Processed: {results['windows_processed']}")
        print(f"Peak RAM: {results['resource_usage']['peak_ram_gb']:.4f} GB (Limit: {MAX_RAM_GB} GB)")
        print(f"Runtime: {results['resource_usage']['total_runtime_hours']:.4f} hours (Limit: {MAX_RUNTIME_HOURS} hours)")
        print(f"RAM Limit Exceeded: {results['resource_usage']['exceeded_ram_limit']}")
        print(f"Runtime Limit Exceeded: {results['resource_usage']['exceeded_runtime_limit']}")
        print("="*60)

        if results['resource_usage']['exceeded_ram_limit'] or results['resource_usage']['exceeded_runtime_limit']:
            print("⚠️  WARNING: Resource limits exceeded!")
            sys.exit(1)
        else:
            print("✓ Resource validation PASSED")
            sys.exit(0)

    except ResourceValidationError as e:
        print(f"\n❌ ResourceValidationError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()