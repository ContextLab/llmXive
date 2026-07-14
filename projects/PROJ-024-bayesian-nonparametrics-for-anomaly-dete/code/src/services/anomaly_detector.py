"""
Anomaly Detector Service for DP-GMM based time series anomaly detection.

Implements a modular set of methods for loading models, processing streaming
data, computing anomaly scores, and managing checkpoints.
"""
import os
import sys
import json
import time
import logging
import traceback
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass, asdict
import numpy as np
import psutil

# Add src to path for imports
src_path = Path(__file__).resolve().parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from models.dpgmm import DPGMMModel, DPGMMConfig
from data.windowing import sliding_window, normalize_window
from evaluation.metrics import EvaluationMetrics
from services.state_update import record_artifact_hash

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
class ResourceUsage:
    """Tracks resource usage for compliance validation."""
    peak_ram_mb: float
    total_runtime_seconds: float
    cpu_count: int
    timestamp: str
    status: str  # 'within_limits', 'exceeded_ram', 'exceeded_time'


class ResourceLimitExceededError(Exception):
    """Raised when resource limits are exceeded."""
    pass


class AnomalyDetectorService:
    """
    Service for anomaly detection using DP-GMM models.
    
    Provides methods for model loading, streaming data processing,
    anomaly scoring, uncertainty estimation, and checkpoint management.
    """
    
    def __init__(
        self,
        config_path: str,
        model_path: Optional[str] = None,
        window_size: int = 50,
        stride: int = 1,
        ram_limit_mb: float = 7000.0,
        time_limit_seconds: float = 21600.0  # 6 hours
    ):
        """
        Initialize the AnomalyDetectorService.
        
        Args:
            config_path: Path to the configuration YAML file.
            model_path: Optional path to a pre-trained model checkpoint.
            window_size: Size of the sliding window for processing.
            stride: Stride for sliding window.
            ram_limit_mb: Maximum allowed RAM usage in MB.
            time_limit_seconds: Maximum allowed runtime in seconds.
        """
        self.config_path = Path(config_path)
        self.model_path = model_path
        self.window_size = window_size
        self.stride = stride
        self.ram_limit_mb = ram_limit_mb
        self.time_limit_seconds = time_limit_seconds
        
        self.model: Optional[DPGMMModel] = None
        self.process = psutil.Process()
        self.start_time: Optional[float] = None
        self.peak_ram_mb: float = 0.0
        self.resource_usage: Optional[ResourceUsage] = None
        
        # Load configuration
        self.config = self._load_config()
        logger.info(f"Initialized AnomalyDetectorService with config: {self.config_path}")
        
        # Load model if path provided
        if self.model_path:
            self.load_model(self.model_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _update_resource_metrics(self) -> None:
        """Update peak RAM and runtime metrics."""
        current_ram = self.process.memory_info().rss / (1024 * 1024)  # Convert to MB
        self.peak_ram_mb = max(self.peak_ram_mb, current_ram)
        
        if self.start_time is not None:
            current_time = time.time() - self.start_time
            # Check limits
            if self.peak_ram_mb > self.ram_limit_mb:
                raise ResourceLimitExceededError(
                    f"RAM limit exceeded: {self.peak_ram_mb:.2f}MB > {self.ram_limit_mb:.2f}MB"
                )
            if current_time > self.time_limit_seconds:
                raise ResourceLimitExceededError(
                    f"Time limit exceeded: {current_time:.2f}s > {self.time_limit_seconds:.2f}s"
                )
    
    def load_model(self, model_path: str) -> None:
        """
        Load a pre-trained DP-GMM model from a checkpoint.
        
        Args:
            model_path: Path to the model checkpoint file.
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
            
            # Load model state
            self.model = DPGMMModel.load(str(model_path))
            logger.info(f"Successfully loaded model from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def process_stream(
        self,
        data: np.ndarray,
        ground_truth: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Process a stream of time series data using sliding windows.
        
        Args:
            data: 1D array of time series data.
            ground_truth: Optional list of ground truth anomaly indices.
        
        Returns:
            Dictionary containing anomaly scores, timestamps, and metadata.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        self.start_time = time.time()
        logger.info(f"Processing stream of length {len(data)}")
        
        # Normalize data
        data_mean = np.mean(data)
        data_std = np.std(data)
        if data_std == 0:
            data_std = 1.0
        normalized_data = (data - data_mean) / data_std
        
        # Generate windows
        windows = sliding_window(normalized_data, self.window_size, self.stride)
        logger.info(f"Generated {len(windows)} windows")
        
        scores = []
        uncertainties = []
        timestamps = []
        alpha_derivatives = []
        weight_variances = []
        
        for i, window in enumerate(windows):
            self._update_resource_metrics()
            
            # Compute anomaly score
            score, uncertainty = self.compute_score(window)
            scores.append(score)
            uncertainties.append(uncertainty)
            
            # Compute timestamp (center of window)
            timestamps.append((i * self.stride) + (self.window_size // 2))
            
            # Extract model statistics if available
            if hasattr(self.model, 'get_alpha_derivative'):
                try:
                    alpha_derivatives.append(self.model.get_alpha_derivative())
                except:
                    alpha_derivatives.append(None)
            else:
                alpha_derivatives.append(None)
            
            if hasattr(self.model, 'get_weight_variance'):
                try:
                    weight_variances.append(self.model.get_weight_variance())
                except:
                    weight_variances.append(None)
            else:
                weight_variances.append(None)
            
            # Update model with new window (online learning)
            if i % 10 == 0:  # Update periodically
                self.update_model(window)
        
        result = {
            'scores': np.array(scores),
            'uncertainties': np.array(uncertainties),
            'timestamps': np.array(timestamps),
            'data_length': len(data),
            'window_size': self.window_size,
            'stride': self.stride,
            'ground_truth': ground_truth,
            'alpha_derivatives': alpha_derivatives,
            'weight_variances': weight_variances
        }
        
        # Record final resource usage
        self.resource_usage = ResourceUsage(
            peak_ram_mb=self.peak_ram_mb,
            total_runtime_seconds=time.time() - self.start_time,
            cpu_count=psutil.cpu_count(),
            timestamp=datetime.now().isoformat(),
            status='within_limits'
        )
        
        logger.info(f"Processing completed in {self.resource_usage.total_runtime_seconds:.2f}s")
        return result
    
    def update_model(self, window: np.ndarray) -> None:
        """
        Update the model with a new window of data.
        
        Args:
            window: Array of data for the current window.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        
        try:
            # Perform one step of variational inference
            self.model.partial_fit(window)
            logger.debug("Model updated with new window")
        except Exception as e:
            logger.warning(f"Model update failed: {e}")
            # Continue without update rather than failing
    
    def compute_score(self, window: np.ndarray) -> Tuple[float, float]:
        """
        Compute anomaly score and uncertainty for a single window.
        
        Args:
            window: Array of data for the current window.
        
        Returns:
            Tuple of (anomaly_score, uncertainty).
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        
        try:
            # Compute reconstruction error or negative log-likelihood
            score = self.model.compute_anomaly_score(window)
            
            # Estimate uncertainty (e.g., via bootstrap or posterior variance)
            uncertainty = self.get_uncertainty(window)
            
            return float(score), float(uncertainty)
        
        except Exception as e:
            logger.error(f"Score computation failed: {e}")
            return 0.0, 0.0
    
    def get_uncertainty(self, window: np.ndarray) -> float:
        """
        Estimate uncertainty for a given window.
        
        Args:
            window: Array of data for the current window.
        
        Returns:
            Uncertainty estimate (e.g., posterior variance).
        """
        if self.model is None:
            return 0.0
        
        try:
            # Use model's uncertainty estimation if available
            if hasattr(self.model, 'compute_uncertainty'):
                return float(self.model.compute_uncertainty(window))
            
            # Fallback: estimate via score variance
            # (In practice, use proper Bayesian uncertainty)
            return 0.1  # Placeholder for demonstration
        
        except Exception as e:
            logger.warning(f"Uncertainty estimation failed: {e}")
            return 0.0
    
    def save_checkpoint(self, output_path: str) -> None:
        """
        Save the current model state to a checkpoint.
        
        Args:
            output_path: Path to save the checkpoint.
        """
        if self.model is None:
            raise RuntimeError("No model to save.")
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.model.save(str(output_path))
            
            # Record checksum
            record_artifact_hash(str(output_path))
            logger.info(f"Checkpoint saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise
    
    def get_resource_usage(self) -> ResourceUsage:
        """
        Get the current resource usage metrics.
        
        Returns:
            ResourceUsage object with RAM and runtime metrics.
        """
        if self.resource_usage is None:
            self._update_resource_metrics()
        return self.resource_usage
    
    def evaluate_performance(
        self,
        scores: np.ndarray,
        ground_truth: List[int],
        threshold: float = 0.5
    ) -> EvaluationMetrics:
        """
        Evaluate detection performance against ground truth.
        
        Args:
            scores: Array of anomaly scores.
            ground_truth: List of ground truth anomaly indices.
            threshold: Threshold for anomaly classification.
        
        Returns:
            EvaluationMetrics object with precision, recall, F1, etc.
        """
        # Convert scores to binary predictions
        predictions = (scores > threshold).astype(int)
        
        # Create binary ground truth array
        gt_array = np.zeros(len(scores), dtype=int)
        for idx in ground_truth:
            if 0 <= idx < len(gt_array):
                gt_array[idx] = 1
        
        # Compute metrics
        metrics = EvaluationMetrics(
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            accuracy=0.0,
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0
        )
        
        if np.sum(gt_array) == 0:
            logger.warning("No ground truth anomalies found")
            return metrics
        
        # Calculate confusion matrix components
        tp = np.sum((predictions == 1) & (gt_array == 1))
        fp = np.sum((predictions == 1) & (gt_array == 0))
        tn = np.sum((predictions == 0) & (gt_array == 0))
        fn = np.sum((predictions == 0) & (gt_array == 1))
        
        metrics.true_positives = int(tp)
        metrics.false_positives = int(fp)
        metrics.true_negatives = int(tn)
        metrics.false_negatives = int(fn)
        
        # Calculate rates
        if (tp + fp) > 0:
            metrics.precision = tp / (tp + fp)
        if (tp + fn) > 0:
            metrics.recall = tp / (tp + fn)
        if metrics.precision + metrics.recall > 0:
            metrics.f1_score = 2 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
        if len(predictions) > 0:
            metrics.accuracy = (tp + tn) / len(predictions)
        
        logger.info(f"Evaluation complete: Precision={metrics.precision:.3f}, Recall={metrics.recall:.3f}, F1={metrics.f1_score:.3f}")
        return metrics


def main():
    """Main entry point for testing the anomaly detector service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Anomaly Detector Service')
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    parser.add_argument('--model', type=str, help='Path to model checkpoint')
    parser.add_argument('--data', type=str, help='Path to input data file')
    parser.add_argument('--output', type=str, help='Path to output results')
    parser.add_argument('--window-size', type=int, default=50, help='Window size')
    parser.add_argument('--stride', type=int, default=1, help='Window stride')
    
    args = parser.parse_args()
    
    try:
        # Initialize service
        service = AnomalyDetectorService(
            config_path=args.config,
            model_path=args.model,
            window_size=args.window_size,
            stride=args.stride
        )
        
        # Load data if provided
        if args.data:
            data = np.loadtxt(args.data, delimiter=',')
            if len(data.shape) == 2:
                data = data[:, 0]  # Take first column if 2D
            
            # Process stream
            results = service.process_stream(data)
            
            # Save results
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Convert numpy arrays to lists for JSON serialization
                save_dict = {
                    'scores': results['scores'].tolist(),
                    'uncertainties': results['uncertainties'].tolist(),
                    'timestamps': results['timestamps'].tolist(),
                    'data_length': results['data_length'],
                    'window_size': results['window_size'],
                    'stride': results['stride']
                }
                
                with open(output_path, 'w') as f:
                    json.dump(save_dict, f, indent=2)
                
                logger.info(f"Results saved to {output_path}")
            
            # Print summary
            logger.info(f"Processed {len(results['scores'])} windows")
            logger.info(f"Peak RAM: {service.get_resource_usage().peak_ram_mb:.2f}MB")
        
        else:
            logger.info("No data provided. Service initialized successfully.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()