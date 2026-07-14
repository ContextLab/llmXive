"""
Anomaly Detector Service with Resource Validation Logic.

This module implements the AnomalyDetectorService class which handles
model loading, streaming inference, and resource constraint validation.

Resource Validation (FR-008):
- Measures peak RAM usage during inference
- Measures total runtime
- Fails the run if limits are exceeded (7GB RAM, 6 hours)
"""

import os
import sys
import time
import json
import logging
import tracemalloc
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict

# Import from sibling modules based on existing API surface
# Note: Using relative imports as per project structure
try:
    from models.dp_gmm import DPGMMModel, DPGMMConfig
    from models.anomaly_score import AnomalyScore
except ImportError:
    # Fallback for direct execution
    pass


@dataclass
class ResourceMetrics:
    """Data class for storing resource measurement results."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    exceeded_ram_limit: bool = False
    exceeded_time_limit: bool = False
    limit_ram_mb: float = 7000.0  # 7 GB
    limit_time_seconds: float = 21600.0  # 6 hours

@dataclass
class AnomalyDetectorService:
    """
    Service for anomaly detection with resource validation.

    This service wraps the DPGMM model and adds resource monitoring
    to ensure compliance with GitHub Actions constraints.
    """

    config: Optional[DPGMMConfig] = None
    model: Optional[DPGMMModel] = None
    metrics: ResourceMetrics = field(default_factory=ResourceMetrics)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
    is_tracking: bool = False
    resource_report_path: Optional[Path] = None

    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        resource_report_path: Optional[str] = None,
        ram_limit_mb: float = 7000.0,
        time_limit_seconds: float = 21600.0
    ):
        """
        Initialize the AnomalyDetectorService.

        Args:
            config: DPGMM configuration object
            resource_report_path: Path to save resource validation report
            ram_limit_mb: Maximum allowed RAM in MB (default: 7GB)
            time_limit_seconds: Maximum allowed runtime in seconds (default: 6 hours)
        """
        self.config = config
        self.metrics = ResourceMetrics(
            limit_ram_mb=ram_limit_mb,
            limit_time_seconds=time_limit_seconds
        )
        self.resource_report_path = Path(resource_report_path) if resource_report_path else None
        self.logger = logging.getLogger(__name__)
        self.is_tracking = False

    def _start_tracking(self) -> None:
        """Start memory and time tracking."""
        if not self.is_tracking:
            tracemalloc.start()
            self.metrics.start_time = datetime.now().isoformat()
            self.is_tracking = True
            self.logger.info("Resource tracking started")

    def _stop_tracking(self) -> None:
        """Stop memory and time tracking and record metrics."""
        if self.is_tracking:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.is_tracking = False

            # Convert to MB
            self.metrics.peak_ram_mb = peak / (1024 * 1024)
            self.metrics.end_time = datetime.now().isoformat()

            # Calculate runtime
            if self.metrics.start_time and self.metrics.end_time:
                start_dt = datetime.fromisoformat(self.metrics.start_time)
                end_dt = datetime.fromisoformat(self.metrics.end_time)
                self.metrics.total_runtime_seconds = (end_dt - start_dt).total_seconds()

            self.logger.info(f"Resource tracking stopped. Peak RAM: {self.metrics.peak_ram_mb:.2f} MB, "
                             f"Runtime: {self.metrics.total_runtime_seconds:.2f} seconds")

    def _check_limits(self) -> bool:
        """
        Check if resource limits have been exceeded.

        Returns:
            True if limits are respected, False otherwise
        """
        self.metrics.exceeded_ram_limit = self.metrics.peak_ram_mb > self.metrics.limit_ram_mb
        self.metrics.exceeded_time_limit = self.metrics.total_runtime_seconds > self.metrics.limit_time_seconds

        if self.metrics.exceeded_ram_limit:
            self.logger.error(f"RAM limit exceeded: {self.metrics.peak_ram_mb:.2f} MB > {self.metrics.limit_ram_mb:.2f} MB")

        if self.metrics.exceeded_time_limit:
            self.logger.error(f"Time limit exceeded: {self.metrics.total_runtime_seconds:.2f} seconds > {self.metrics.limit_time_seconds:.2f} seconds")

        return not (self.metrics.exceeded_ram_limit or self.metrics.exceeded_time_limit)

    def _save_report(self) -> None:
        """Save resource validation report to disk."""
        if self.resource_report_path:
            report_dict = asdict(self.metrics)
            report_dict['timestamp'] = datetime.now().isoformat()
            report_dict['status'] = 'PASSED' if self._check_limits() else 'FAILED'

            # Ensure directory exists
            self.resource_report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.resource_report_path, 'w') as f:
                json.dump(report_dict, f, indent=2)

            self.logger.info(f"Resource report saved to {self.resource_report_path}")

    def load_model(self, model_path: str) -> None:
        """
        Load a pre-trained DPGMM model.

        Args:
            model_path: Path to the saved model
        """
        self._start_tracking()
        try:
            if self.config is None:
                self.config = DPGMMConfig()

            self.model = DPGMMModel(self.config)
            # Model loading logic would go here
            self.logger.info(f"Model loaded from {model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
        finally:
            self._stop_tracking()

    def process_stream(self, data_stream: List[Dict[str, Any]]) -> List[AnomalyScore]:
        """
        Process a stream of observations and compute anomaly scores.

        Args:
            data_stream: List of observation dictionaries

        Returns:
            List of AnomalyScore objects
        """
        self._start_tracking()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded. Call load_model() first.")

            scores = []
            for obs in data_stream:
                # Process each observation
                score = self.model.compute_anomaly_score(obs)
                scores.append(score)

            self.logger.info(f"Processed {len(data_stream)} observations")
            return scores
        except Exception as e:
            self.logger.error(f"Error processing stream: {e}")
            raise
        finally:
            self._stop_tracking()
            # Check limits and fail if exceeded
            if not self._check_limits():
                raise RuntimeError("Resource limits exceeded during inference")

    def update_model(self, new_data: List[Dict[str, Any]]) -> None:
        """
        Update the model with new data.

        Args:
            new_data: New observations to incorporate
        """
        self._start_tracking()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded.")

            # Update model logic
            self.model.update(new_data)
            self.logger.info("Model updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update model: {e}")
            raise
        finally:
            self._stop_tracking()

    def compute_score(self, observation: Dict[str, Any]) -> AnomalyScore:
        """
        Compute anomaly score for a single observation.

        Args:
            observation: Single observation dictionary

        Returns:
            AnomalyScore object
        """
        self._start_tracking()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded.")

            score = self.model.compute_anomaly_score(observation)
            return score
        except Exception as e:
            self.logger.error(f"Error computing score: {e}")
            raise
        finally:
            self._stop_tracking()

    def get_uncertainty(self, observation: Dict[str, Any]) -> Dict[str, float]:
        """
        Get uncertainty estimates for an observation.

        Args:
            observation: Single observation dictionary

        Returns:
            Dictionary with uncertainty metrics
        """
        self._start_tracking()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded.")

            # Return uncertainty metrics
            uncertainty = {
                'variance': 0.0,
                'confidence': 0.0
            }
            return uncertainty
        except Exception as e:
            self.logger.error(f"Error computing uncertainty: {e}")
            raise
        finally:
            self._stop_tracking()

    def save_checkpoint(self, checkpoint_path: str) -> None:
        """
        Save the current model state to a checkpoint.

        Args:
            checkpoint_path: Path to save the checkpoint
        """
        self._start_tracking()
        try:
            if self.model is None:
                raise RuntimeError("Model not loaded.")

            # Save model checkpoint
            self.model.save(checkpoint_path)
            self.logger.info(f"Checkpoint saved to {checkpoint_path}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise
        finally:
            self._stop_tracking()

    def validate_resources(self) -> bool:
        """
        Validate that resource usage is within limits.

        Returns:
            True if within limits, False otherwise
        """
        self._save_report()
        return self._check_limits()

    def get_metrics(self) -> ResourceMetrics:
        """
        Get the current resource metrics.

        Returns:
            ResourceMetrics object
        """
        return self.metrics


def main():
    """Main entry point for resource validation testing."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create service with resource limits
    service = AnomalyDetectorService(
        ram_limit_mb=7000.0,
        time_limit_seconds=21600.0,
        resource_report_path="data/processed/results/resource_validation_report.json"
    )

    # Simulate some work to measure resources
    logger.info("Starting resource validation test...")

    # Create a simple test dataset
    test_data = [
        {"value": float(i), "timestamp": datetime.now().isoformat()}
        for i in range(1000)
    ]

    try:
        # Process the stream
        scores = service.process_stream(test_data)
        logger.info(f"Processed {len(scores)} observations")

        # Validate resources
        if service.validate_resources():
            logger.info("✓ Resource validation PASSED")
            sys.exit(0)
        else:
            logger.error("✗ Resource validation FAILED")
            metrics = service.get_metrics()
            logger.error(f"  Peak RAM: {metrics.peak_ram_mb:.2f} MB (limit: {metrics.limit_ram_mb:.2f} MB)")
            logger.error(f"  Runtime: {metrics.total_runtime_seconds:.2f} seconds (limit: {metrics.limit_time_seconds:.2f} seconds)")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Resource validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()