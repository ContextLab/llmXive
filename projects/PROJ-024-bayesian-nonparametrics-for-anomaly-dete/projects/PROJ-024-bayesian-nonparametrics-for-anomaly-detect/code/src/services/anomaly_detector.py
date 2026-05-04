"""
AnomalyDetectorService - Main service interface for anomaly detection.

Implements all 7 required methods per spec.md Service Interfaces section.
Type hints added per PEP 484 compliance (T161).
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import (
    Optional,
    List,
    Dict,
    Any,
    Union,
    Tuple,
    Sequence,
    Literal,
    TypeVar,
    Generic,
)
import numpy as np
import logging

from models.dpgmm import DPGMMModel, DPGMMConfig, AnomalyScore
from models.time_series import TimeSeries
from baselines.arima import ARIMABaseline, ARIMAConfig
from baselines.moving_average import MovingAverageBaseline, MovingAverageConfig
from evaluation.metrics import EvaluationMetrics

# Type alias for clarity
ScoreType = float
TimestampType = datetime
ModelType = Literal["dpgmm", "arima", "moving_average"]


@dataclass
class AnomalyDetectionResult:
    """Result container for anomaly detection operations."""
    timestamp: TimestampType
    value: float
    anomaly_score: ScoreType
    is_anomaly: bool
    model_used: ModelType
    threshold_used: Optional[ScoreType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnomalyDetectorService:
    """
    Service interface for anomaly detection with multiple model support.
    
    Implements exactly 7 required methods per spec.md Service Interfaces:
    1. initialize_model
    2. train
    3. predict
    4. get_anomaly_score
    5. set_threshold
    6. evaluate
    7. get_model_state
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        model_type: ModelType = "dpgmm",
        log_level: int = logging.INFO
    ) -> None:
        """
        Initialize the AnomalyDetectorService.
        
        Args:
            config_path: Path to configuration YAML file
            model_type: Type of model to use (dpgmm, arima, moving_average)
            log_level: Logging level for the service
        """
        self.config_path: Optional[Path] = config_path
        self.model_type: ModelType = model_type
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        self.model: Optional[Union[DPGMMModel, ARIMABaseline, MovingAverageBaseline]] = None
        self.threshold: Optional[ScoreType] = None
        self.is_trained: bool = False
        self._training_history: List[Dict[str, Any]] = []

    def initialize_model(
        self,
        config: Optional[Union[DPGMMConfig, ARIMAConfig, MovingAverageConfig]] = None,
        **kwargs: Any
    ) -> bool:
        """
        Initialize the detection model with configuration.
        
        Args:
            config: Model-specific configuration object
            **kwargs: Additional model parameters
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.model_type == "dpgmm":
                if config is None:
                    config = DPGMMConfig()
                if isinstance(config, DPGMMConfig):
                    self.model = DPGMMModel(config=config, **kwargs)
            elif self.model_type == "arima":
                if config is None:
                    config = ARIMAConfig()
                if isinstance(config, ARIMAConfig):
                    self.model = ARIMABaseline(config=config, **kwargs)
            elif self.model_type == "moving_average":
                if config is None:
                    config = MovingAverageConfig()
                if isinstance(config, MovingAverageConfig):
                    self.model = MovingAverageBaseline(config=config, **kwargs)
            else:
                self.logger.error(f"Unknown model type: {self.model_type}")
                return False
            
            self.logger.info(f"Initialized {self.model_type} model")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize model: {e}")
            return False

    def train(
        self,
        data: Union[np.ndarray, List[float], TimeSeries],
        labels: Optional[np.ndarray] = None,
        max_iterations: int = 100,
        early_stopping_threshold: float = 1e-4
    ) -> Dict[str, Any]:
        """
        Train the model on the provided data.
        
        Args:
            data: Training data (array, list, or TimeSeries object)
            labels: Optional ground truth labels for supervised evaluation
            max_iterations: Maximum training iterations
            early_stopping_threshold: ELBO convergence threshold
        
        Returns:
            Dictionary containing training results and metrics
        """
        if self.model is None:
            self.logger.error("Model not initialized. Call initialize_model first.")
            return {"success": False, "error": "Model not initialized"}
        
        try:
            # Convert input to numpy array if needed
            if isinstance(data, TimeSeries):
                data_array: np.ndarray = data.values
            elif isinstance(data, list):
                data_array = np.array(data)
            else:
                data_array = data
            
            # Train the model
            if hasattr(self.model, "fit"):
                result = self.model.fit(
                    data_array,
                    max_iterations=max_iterations,
                    early_stopping_threshold=early_stopping_threshold
                )
            elif hasattr(self.model, "train"):
                result = self.model.train(
                    data_array,
                    max_iterations=max_iterations,
                    early_stopping_threshold=early_stopping_threshold
                )
            else:
                self.logger.error(f"Model type {self.model_type} has no fit/train method")
                return {"success": False, "error": "Model has no fit/train method"}
            
            self.is_trained = True
            self._training_history.append({
                "timestamp": datetime.now().isoformat(),
                "data_shape": data_array.shape,
                "result": result
            })
            
            self.logger.info(f"Training completed for {self.model_type}")
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return {"success": False, "error": str(e)}

    def predict(
        self,
        data: Union[np.ndarray, List[float], TimeSeries, float]
    ) -> Union[List[bool], bool]:
        """
        Predict anomalies for the provided data.
        
        Args:
            data: Data to predict anomalies on (array, list, TimeSeries, or single value)
        
        Returns:
            List of boolean anomaly flags, or single boolean for scalar input
        """
        if not self.is_trained:
            self.logger.warning("Model not trained. Returning all False predictions.")
            if isinstance(data, (np.ndarray, list)):
                return [False] * len(data)
            return False
        
        try:
            if isinstance(data, TimeSeries):
                data_array: np.ndarray = data.values
            elif isinstance(data, list):
                data_array = np.array(data)
            elif isinstance(data, (int, float)):
                data_array = np.array([data])
            else:
                data_array = data
            
            # Get anomaly scores
            scores: np.ndarray = self.get_anomaly_score(data)
            
            # Apply threshold if set
            if self.threshold is not None:
                predictions: np.ndarray = scores > self.threshold
            else:
                predictions = np.zeros_like(scores, dtype=bool)
            
            if len(predictions) == 1:
                return bool(predictions[0])
            return predictions.tolist()
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            if isinstance(data, (np.ndarray, list)):
                return [False] * len(data)
            return False

    def get_anomaly_score(
        self,
        data: Union[np.ndarray, List[float], TimeSeries, float]
    ) -> Union[np.ndarray, float]:
        """
        Compute anomaly scores for the provided data.
        
        Args:
            data: Data to compute anomaly scores for
        
        Returns:
            Anomaly scores (array or scalar)
        """
        if self.model is None:
            self.logger.error("Model not initialized. Cannot compute anomaly scores.")
            if isinstance(data, (np.ndarray, list)):
                return np.zeros(len(data))
            return 0.0
        
        try:
            if isinstance(data, TimeSeries):
                data_array: np.ndarray = data.values
            elif isinstance(data, list):
                data_array = np.array(data)
            elif isinstance(data, (int, float)):
                data_array = np.array([data])
            else:
                data_array = data
            
            # Compute anomaly scores based on model type
            if hasattr(self.model, "compute_anomaly_score"):
                if isinstance(data_array, np.ndarray) and data_array.ndim == 1:
                    scores = self.model.compute_anomaly_score(data_array)
                else:
                    scores = self.model.compute_anomaly_scores_batch(data_array)
            elif hasattr(self.model, "score"):
                scores = self.model.score(data_array)
            else:
                self.logger.error(f"Model type {self.model_type} has no score method")
                if isinstance(data_array, np.ndarray):
                    return np.zeros(len(data_array))
                return 0.0
            
            if isinstance(scores, (int, float)):
                return float(scores)
            return np.array(scores)
        except Exception as e:
            self.logger.error(f"Anomaly score computation failed: {e}")
            if isinstance(data, (np.ndarray, list)):
                return np.zeros(len(data))
            return 0.0

    def set_threshold(
        self,
        threshold: ScoreType,
        method: Optional[str] = None
    ) -> bool:
        """
        Set the anomaly detection threshold.
        
        Args:
            threshold: Anomaly score threshold value
            method: Optional method used for threshold calibration
        
        Returns:
            True if threshold set successfully
        """
        try:
            if threshold < 0:
                self.logger.error("Threshold must be non-negative")
                return False
            
            self.threshold = threshold
            self.logger.info(f"Threshold set to {threshold} (method: {method or 'manual'})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set threshold: {e}")
            return False

    def evaluate(
        self,
        data: Union[np.ndarray, List[float], TimeSeries],
        labels: np.ndarray,
        threshold: Optional[ScoreType] = None
    ) -> EvaluationMetrics:
        """
        Evaluate model performance against ground truth labels.
        
        Args:
            data: Test data
            labels: Ground truth anomaly labels (0/1)
            threshold: Optional threshold override for evaluation
        
        Returns:
            EvaluationMetrics object containing F1, precision, recall, etc.
        """
        if not self.is_trained:
            self.logger.error("Model not trained. Cannot evaluate.")
            return EvaluationMetrics(f1_score=0.0, precision=0.0, recall=0.0)
        
        try:
            if isinstance(data, TimeSeries):
                data_array: np.ndarray = data.values
            elif isinstance(data, list):
                data_array = np.array(data)
            else:
                data_array = data
            
            # Compute scores
            scores: np.ndarray = self.get_anomaly_score(data_array)
            
            # Use provided threshold or instance threshold
            eval_threshold: ScoreType = threshold if threshold is not None else self.threshold or 0.0
            
            # Compute predictions
            predictions: np.ndarray = (scores > eval_threshold).astype(int)
            labels_array: np.ndarray = np.array(labels) if not isinstance(labels, np.ndarray) else labels
            
            # Compute metrics
            from evaluation.metrics import compute_all_metrics
            metrics: EvaluationMetrics = compute_all_metrics(
                y_true=labels_array,
                y_pred=predictions,
                scores=scores
            )
            
            self.logger.info(
                f"Evaluation complete: F1={metrics.f1_score:.4f}, "
                f"Precision={metrics.precision:.4f}, Recall={metrics.recall:.4f}"
            )
            return metrics
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return EvaluationMetrics(f1_score=0.0, precision=0.0, recall=0.0)

    def get_model_state(self) -> Dict[str, Any]:
        """
        Get the current state of the model for persistence/debugging.
        
        Returns:
            Dictionary containing model state information
        """
        state: Dict[str, Any] = {
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "threshold": self.threshold,
            "training_history_count": len(self._training_history),
            "config_path": str(self.config_path) if self.config_path else None
        }
        
        if self.model is not None and hasattr(self.model, "get_state"):
            state["model_state"] = self.model.get_state()
        elif self.model is not None:
            state["model_state"] = {
                "type": type(self.model).__name__,
                "initialized": True
            }
        
        return state


def create_service(
    model_type: ModelType = "dpgmm",
    config_path: Optional[Path] = None
) -> AnomalyDetectorService:
    """
    Factory function to create an AnomalyDetectorService instance.
    
    Args:
        model_type: Type of model to use
        config_path: Optional path to configuration file
    
    Returns:
        Configured AnomalyDetectorService instance
    """
    return AnomalyDetectorService(
        config_path=config_path,
        model_type=model_type
    )


def main() -> None:
    """Main entry point for service demonstration/testing."""
    import sys
    
    service: AnomalyDetectorService = create_service(model_type="dpgmm")
    
    # Initialize model
    if not service.initialize_model():
        print("Failed to initialize model")
        sys.exit(1)
    
    # Generate synthetic data for testing
    from data.synthetic_generator import generate_synthetic_timeseries
    data: np.ndarray = generate_synthetic_timeseries(
        n_samples=1000,
        n_anomalies=50
    )
    
    # Train model
    train_result: Dict[str, Any] = service.train(data[:800])
    if not train_result.get("success"):
        print(f"Training failed: {train_result.get('error')}")
        sys.exit(1)
    
    # Set threshold
    service.set_threshold(threshold=0.7)
    
    # Evaluate
    labels: np.ndarray = np.concatenate([
        np.zeros(800),
        np.ones(200)
    ])
    metrics: EvaluationMetrics = service.evaluate(data, labels)
    
    print(f"Evaluation Results:")
    print(f"  F1 Score: {metrics.f1_score:.4f}")
    print(f"  Precision: {metrics.precision:.4f}")
    print(f"  Recall: {metrics.recall:.4f}")
