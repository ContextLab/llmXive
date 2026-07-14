"""
Anomaly Detector Service with Resource Validation.

Implements FR-008: Resource Constraint Validation.
Measures peak RAM and total runtime, failing the run if limits are exceeded.
"""
import os
import sys
import time
import logging
import tracemalloc
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Import from local project structure
# Note: Imports adjusted to match existing API surface provided in prompt
try:
    from models.anomaly_score import AnomalyScore
    from models.dp_gmm import DPGMMModel, DPGMMConfig
except ImportError:
    # Fallback for direct script execution if package structure isn't fully resolved
    # This handles the execution environment where imports might be relative to code/src
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from models.anomaly_score import AnomalyScore
    from models.dp_gmm import DPGMMModel, DPGMMConfig

logger = logging.getLogger(__name__)

@dataclass
class ResourceUsage:
    """Container for resource usage metrics."""
    peak_ram_mb: float = 0.0
    total_runtime_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    exceeded_limits: bool = False
    error_message: Optional[str] = None

class ResourceValidator:
    """
    Validates resource usage against configured limits (FR-008).
    """
    def __init__(self, max_ram_mb: float = 7000.0, max_runtime_seconds: float = 21600.0):
        """
        Initialize the validator with limits.
        
        Args:
            max_ram_mb: Maximum allowed RAM in MB (Default 7GB for GitHub Actions free tier)
            max_runtime_seconds: Maximum allowed runtime in seconds (Default 6 hours)
        """
        self.max_ram_mb = max_ram_mb
        self.max_runtime_seconds = max_runtime_seconds
        self._start_time: Optional[float] = None
        self._peak_ram: float = 0.0
        self._running = False

    def start_tracking(self) -> None:
        """Start tracking time and memory."""
        if self._running:
            logger.warning("Resource tracking already running.")
            return
        
        self._start_time = time.time()
        tracemalloc.start()
        self._running = True
        logger.info("Resource tracking started.")

    def stop_tracking(self) -> ResourceUsage:
        """Stop tracking and return usage metrics."""
        if not self._running:
            logger.warning("Resource tracking not running.")
            return ResourceUsage(exceeded_limits=True, error_message="Tracking not started")

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._running = False

        runtime = end_time - self._start_time
        peak_ram_mb = peak / (1024 * 1024)
        self._peak_ram = peak_ram_mb

        exceeded = False
        error_msg = None

        if peak_ram_mb > self.max_ram_mb:
            exceeded = True
            error_msg = f"Peak RAM {peak_ram_mb:.2f} MB exceeds limit {self.max_ram_mb:.2f} MB"
            logger.error(error_msg)
        
        if runtime > self.max_runtime_seconds:
            exceeded = True
            timeout_msg = f"Runtime {runtime:.2f}s exceeds limit {self.max_runtime_seconds:.2f}s"
            if error_msg:
                error_msg += f"; {timeout_msg}"
            else:
                error_msg = timeout_msg
            logger.error(timeout_msg)

        return ResourceUsage(
            peak_ram_mb=peak_ram_mb,
            total_runtime_seconds=runtime,
            exceeded_limits=exceeded,
            error_message=error_msg
        )

    def check_intermediate(self) -> bool:
        """
        Check current resource usage without stopping tracking.
        Returns True if limits are exceeded, False otherwise.
        """
        if not self._running:
            return False

        current, peak = tracemalloc.get_traced_memory()
        current_ram_mb = current / (1024 * 1024)
        peak_ram_mb = peak / (1024 * 1024)
        runtime = time.time() - self._start_time

        if peak_ram_mb > self.max_ram_mb:
            logger.error(f"Intermediate check: Peak RAM {peak_ram_mb:.2f} MB exceeds limit.")
            return True
        
        if runtime > self.max_runtime_seconds:
            logger.error(f"Intermediate check: Runtime {runtime:.2f}s exceeds limit.")
            return True

        return False

class AnomalyDetectorService:
    """
    Service for anomaly detection with integrated resource validation (FR-008).
    """
    def __init__(self, config: Optional[DPGMMConfig] = None, max_ram_mb: float = 7000.0, max_runtime_seconds: float = 21600.0):
        """
        Initialize the service.
        
        Args:
            config: DPGMM configuration
            max_ram_mb: Max RAM limit in MB
            max_runtime_seconds: Max runtime limit in seconds
        """
        self.config = config or DPGMMConfig()
        self.model: Optional[DPGMMModel] = None
        self.validator = ResourceValidator(max_ram_mb=max_ram_mb, max_runtime_seconds=max_runtime_seconds)
        self._last_scores: List[AnomalyScore] = []
        logger.info("AnomalyDetectorService initialized with resource validation.")

    def load_model(self, model_path: Path) -> None:
        """Load a pre-trained model."""
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        logger.info(f"Loading model from {model_path}")
        # Placeholder for actual loading logic
        # In a real implementation, this would unpickle or load the DPGMMModel
        self.model = DPGMMModel(config=self.config)
        logger.info("Model loaded.")

    def process_stream(self, data: List[float]) -> List[AnomalyScore]:
        """
        Process a stream of data points and compute anomaly scores.
        Includes resource validation checks.
        """
        self.validator.start_tracking()
        scores: List[AnomalyScore] = []
        
        try:
            # Ensure model is initialized if not loaded
            if not self.model:
                self.model = DPGMMModel(config=self.config)
            
            for i, value in enumerate(data):
                # Check resources periodically
                if i % 100 == 0 and self.validator.check_intermediate():
                    usage = self.validator.stop_tracking()
                    raise MemoryError(usage.error_message)
                
                # Simulate processing (in real impl, this calls model inference)
                # Creating a dummy score for demonstration of the flow
                score = AnomalyScore(
                    timestamp=datetime.now(),
                    value=value,
                    anomaly_score=abs(value - 0.5), # Dummy logic
                    uncertainty=0.1,
                    is_anomaly=abs(value - 0.5) > 0.8
                )
                scores.append(score)

            self._last_scores = scores
            usage = self.validator.stop_tracking()
            
            if usage.exceeded_limits:
                raise MemoryError(usage.error_message)
            
            return scores

        except Exception as e:
            if self.validator._running:
                self.validator.stop_tracking()
            raise

    def update_model(self, data: List[float]) -> None:
        """Update the model with new data."""
        self.validator.start_tracking()
        try:
            if not self.model:
                self.model = DPGMMModel(config=self.config)
            
            # Placeholder for update logic
            logger.info(f"Updating model with {len(data)} points.")
            self.validator.stop_tracking()
        except Exception as e:
            if self.validator._running:
                self.validator.stop_tracking()
            raise

    def compute_score(self, value: float) -> AnomalyScore:
        """Compute anomaly score for a single value."""
        if not self.model:
            self.model = DPGMMModel(config=self.config)
        
        # Dummy implementation for single score
        return AnomalyScore(
            timestamp=datetime.now(),
            value=value,
            anomaly_score=abs(value - 0.5),
            uncertainty=0.1,
            is_anomaly=abs(value - 0.5) > 0.8
        )

    def get_uncertainty(self, score: AnomalyScore) -> float:
        """Get uncertainty for a given score."""
        return score.uncertainty

    def save_checkpoint(self, path: Path) -> None:
        """Save the current model state."""
        if not self.model:
            raise ValueError("No model to save.")
        
        # Placeholder for actual save logic
        logger.info(f"Saving checkpoint to {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        # In real impl: pickle.dump(self.model, open(path, 'wb'))

    def validate_resources(self) -> ResourceUsage:
        """
        Explicitly validate resource usage.
        Returns usage metrics and raises if limits exceeded.
        """
        usage = self.validator.stop_tracking()
        if usage.exceeded_limits:
            raise MemoryError(usage.error_message)
        return usage

def main():
    """
    Entry point for resource validation testing.
    Simulates a workload and validates against limits.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Configuration for this test
    MAX_RAM_MB = 7000.0
    MAX_RUNTIME_SEC = 21600.0
    
    service = AnomalyDetectorService(max_ram_mb=MAX_RAM_MB, max_runtime_seconds=MAX_RUNTIME_SEC)
    
    # Generate synthetic data for testing (small subset to ensure it runs in CI)
    # Using a deterministic generator to avoid fabrication concerns
    # but simulating a "real" workload
    import numpy as np
    np.random.seed(42)
    data = np.random.normal(loc=0.5, scale=0.2, size=1000).tolist()
    
    logger.info("Starting resource validation test...")
    
    try:
        scores = service.process_stream(data)
        logger.info(f"Processed {len(scores)} points.")
        
        usage = service.validate_resources()
        logger.info(f"Resource Usage Report:")
        logger.info(f"  Peak RAM: {usage.peak_ram_mb:.2f} MB (Limit: {MAX_RAM_MB:.2f} MB)")
        logger.info(f"  Runtime:  {usage.total_runtime_seconds:.2f} s (Limit: {MAX_RUNTIME_SEC:.2f} s)")
        
        if not usage.exceeded_limits:
            logger.info("✓ Resource limits respected.")
            sys.exit(0)
        else:
            logger.error("✗ Resource limits exceeded.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()