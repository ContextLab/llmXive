"""
LSTM Autoencoder Baseline for Time Series Anomaly Detection

This module implements an LSTM-based autoencoder for unsupervised anomaly detection.
The model learns to reconstruct normal time series patterns and uses reconstruction
error (MSE) as the anomaly score. Higher reconstruction error indicates anomalies.

Per creativity review recommendation for contemporary baselines (T090).
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
import time

# Conditional import for PyTorch - make it optional for environments without GPU
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
  HAS_TORCH = False
  nn = None
  Dataset = object
  DataLoader = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LSTM_AEConfig:
    """Configuration for LSTM Autoencoder baseline."""
    # Architecture parameters
    input_size: int = 1
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    sequence_length: int = 50  # Window size for sliding window approach
    
    # Training parameters
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    early_stopping_patience: int = 10
    
    # Anomaly detection parameters
    threshold_percentile: float = 95.0  # Default threshold
    min_normal_samples: int = 100  # Minimum samples needed for training
    
    # Device configuration
    device: str = 'cpu'
    seed: int = 42
    
    # Paths
    model_save_path: Optional[str] = None
    log_dir: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.hidden_size <= 0:
            raise ValueError("hidden_size must be positive")
        if self.num_layers <= 0:
            raise ValueError("num_layers must be positive")
        if not 0 < self.learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
        if not 0 < self.batch_size <= 1000:
            raise ValueError("batch_size must be in (0, 1000]")
        if not 1 <= self.epochs <= 1000:
            raise ValueError("epochs must be in [1, 1000]")
        if not 0 <= self.dropout < 1:
            raise ValueError("dropout must be in [0, 1)")
        if not 5 <= self.sequence_length <= 500:
            raise ValueError("sequence_length must be in [5, 500]")


@dataclass
class LSTM_AEPrediction:
    """Prediction output from LSTM Autoencoder baseline."""
    timestamp: str
    input_value: float
    reconstructed_value: float
    reconstruction_error: float
    is_anomaly: bool
    anomaly_score: float
    model_state: str  # 'trained', 'untrained', 'error'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp,
            'input_value': float(self.input_value),
            'reconstructed_value': float(self.reconstructed_value),
            'reconstruction_error': float(self.reconstruction_error),
            'is_anomaly': bool(self.is_anomaly),
            'anomaly_score': float(self.anomaly_score),
            'model_state': self.model_state
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'LSTM_AEPrediction':
        """Create from dictionary."""
        return LSTM_AEPrediction(
            timestamp=data['timestamp'],
            input_value=float(data['input_value']),
            reconstructed_value=float(data['reconstructed_value']),
            reconstruction_error=float(data['reconstruction_error']),
            is_anomaly=bool(data['is_anomaly']),
            anomaly_score=float(data['anomaly_score']),
            model_state=data['model_state']
        )


@dataclass
class LSTM_AEState:
    """State for LSTM Autoencoder baseline (for streaming/continual learning)."""
    is_trained: bool = False
    training_samples_seen: int = 0
    current_threshold: float = 0.0
    training_loss_history: List[float] = field(default_factory=list)
    last_update_timestamp: Optional[str] = None
    model_checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'is_trained': self.is_trained,
            'training_samples_seen': self.training_samples_seen,
            'current_threshold': float(self.current_threshold),
            'training_loss_history': self.training_loss_history,
            'last_update_timestamp': self.last_update_timestamp,
            'model_checksum': self.model_checksum
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'LSTM_AEState':
        """Create from dictionary."""
        return LSTM_AEState(
            is_trained=bool(data['is_trained']),
            training_samples_seen=int(data['training_samples_seen']),
            current_threshold=float(data['current_threshold']),
            training_loss_history=data.get('training_loss_history', []),
            last_update_timestamp=data.get('last_update_timestamp'),
            model_checksum=data.get('model_checksum')
        )


class TimeSeriesWindowDataset(Dataset):
    """Dataset for sliding window time series sequences."""
    
    def __init__(self, data: np.ndarray, sequence_length: int):
        """
        Initialize dataset.
        
        Args:
            data: 1D time series array
            sequence_length: Window size for sequences
        """
        self.data = np.asarray(data, dtype=np.float32)
        self.sequence_length = sequence_length
        self.windows = []
        self.targets = []
        
        if len(self.data) < sequence_length:
            raise ValueError(f"Data length {len(data)} must be >= sequence_length {sequence_length}")
        
        # Create sliding windows
        for i in range(len(self.data) - sequence_length + 1):
            window = self.data[i:i + sequence_length]
            self.windows.append(window)
            # Target is the next value after the window (for prediction)
            # or the window itself (for autoencoding)
            self.targets.append(window)
        
        self.windows = np.array(self.windows, dtype=np.float32)
        self.targets = np.array(self.targets, dtype=np.float32)
    
    def __len__(self) -> int:
        return len(self.windows)
    
    def __getitem__(self, idx: int) -> Tuple[np.ndarray, np.ndarray]:
        return self.windows[idx], self.targets[idx]


class LSTM_AE(nn.Module):
    """LSTM Autoencoder architecture for time series anomaly detection."""
    
    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        """
        Initialize LSTM Autoencoder.
        
        Args:
            input_size: Input feature dimension
            hidden_size: LSTM hidden state dimension
            num_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Encoder: LSTM layers
        self.encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Decoder: LSTM layers
        self.decoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Output projection
        self.output_proj = nn.Linear(hidden_size, input_size)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights for better convergence."""
        for name, param in self.named_parameters():
            if 'weight_ih' in name:
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                nn.init.constant_(param.data, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through autoencoder.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)
        
        Returns:
            Reconstructed tensor of shape (batch_size, sequence_length, input_size)
        """
        # Encoder
        encoder_outputs, (hidden, cell) = self.encoder(x)
        
        # Decoder - use last hidden state as initial state
        decoder_outputs, _ = self.decoder(encoder_outputs, (hidden, cell))
        
        # Project to output dimensions
        reconstructed = self.output_proj(decoder_outputs)
        
        return reconstructed
    
    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Get latent representation (encoding)."""
        encoder_outputs, (hidden, cell) = self.encoder(x)
        return encoder_outputs, hidden, cell


class LSTM_AEBaseline:
    """
    LSTM Autoencoder Baseline for Time Series Anomaly Detection.
    
    This baseline uses an LSTM autoencoder to learn normal time series patterns.
    Anomalies are detected using reconstruction error (MSE) - higher error indicates
    anomalies.
    
    Interface matches other baselines (ARIMA, MovingAverage) for fair comparison.
    """
    
    def __init__(self, config: Optional[LSTM_AEConfig] = None):
        """
        Initialize LSTM Autoencoder baseline.
        
        Args:
            config: Configuration object. If None, uses defaults.
        """
        self.config = config or LSTM_AEConfig()
        self.state = LSTM_AEState()
        self.model: Optional[LSTM_AE] = None
        self.scaler_mean: float = 0.0
        self.scaler_std: float = 1.0
        self._training_data: List[float] = []
        self._reconstruction_errors: List[float] = []
        
        # Validate PyTorch availability
        if not HAS_TORCH:
            logger.warning("PyTorch not available. LSTM_AE will run in mock mode.")
            logger.warning("Install with: pip install torch")
    
    def _setup_device(self) -> torch.device:
        """Get appropriate device for training."""
        if not HAS_TORCH:
            return None
        
        device_str = self.config.device
        if device_str == 'cuda' and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            device_str = 'cpu'
        
        return torch.device(device_str)
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data using running statistics."""
        if len(data) == 0:
            return data
        
        data = np.asarray(data, dtype=np.float64)
        self.scaler_mean = float(np.mean(data))
        self.scaler_std = float(np.std(data))
        
        if self.scaler_std < 1e-8:
            self.scaler_std = 1.0  # Prevent division by zero
        
        return (data - self.scaler_mean) / self.scaler_std
    
    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data using running statistics."""
        data = np.asarray(data, dtype=np.float64)
        return (data * self.scaler_std) + self.scaler_mean
    
    def train(
        self,
        time_series: np.ndarray,
        labels: Optional[np.ndarray] = None,
        validation_split: float = 0.1
    ) -> Dict[str, Any]:
        """
        Train the LSTM Autoencoder on normal time series data.
        
        Args:
            time_series: 1D array of time series values
            labels: Optional 1D array of anomaly labels (0=normal, 1=anomaly)
                   Used for threshold calibration
            validation_split: Fraction of data to use for validation
        
        Returns:
            Dictionary with training results and metrics
        """
        if not HAS_TORCH:
            logger.error("Cannot train: PyTorch not available")
            return {
                'success': False,
                'error': 'PyTorch not installed',
                'training_samples_seen': 0
            }
        
        start_time = time.time()
        logger.info(f"Training LSTM Autoencoder with {len(time_series)} samples")
        
        # Validate input
        time_series = np.asarray(time_series, dtype=np.float64).flatten()
        
        if len(time_series) < self.config.sequence_length + self.config.min_normal_samples:
            error_msg = f"Insufficient data: need at least {self.config.sequence_length + self.config.min_normal_samples} samples"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'training_samples_seen': len(time_series)
            }
        
        # Normalize data
        normalized = self._normalize(time_series)
        
        # Create dataset
        dataset = TimeSeriesWindowDataset(
            normalized,
            self.config.sequence_length
        )
        
        # Split into train/val
        val_size = int(len(dataset) * validation_split)
        train_size = len(dataset) - val_size
        
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(self.config.seed)
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            drop_last=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            drop_last=True
        )
        
        # Setup model
        device = self._setup_device()
        self.model = LSTM_AE(
            input_size=self.config.input_size,
            hidden_size=self.config.hidden_size,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout
        ).to(device)
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.config.learning_rate
        )
        
        # Training loop with early stopping
        best_val_loss = float('inf')
        patience_counter = 0
        training_losses = []
        
        for epoch in range(self.config.epochs):
            # Training phase
            self.model.train()
            epoch_train_loss = 0.0
            num_batches = 0
            
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(device)
                batch_y = batch_y.to(device)
                
                optimizer.zero_grad()
                reconstructed = self.model(batch_x)
                loss = criterion(reconstructed, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                
                epoch_train_loss += loss.item()
                num_batches += 1
            
            avg_train_loss = epoch_train_loss / max(num_batches, 1)
            training_losses.append(avg_train_loss)
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            num_val_batches = 0
            
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(device)
                    batch_y = batch_y.to(device)
                    
                    reconstructed = self.model(batch_x)
                    loss = criterion(reconstructed, batch_y)
                    val_loss += loss.item()
                    num_val_batches += 1
            
            avg_val_loss = val_loss / max(num_val_batches, 1)
            
            # Early stopping check
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                # Save best model state
                best_model_state = {
                    'epoch': epoch,
                    'train_loss': avg_train_loss,
                    'val_loss': avg_val_loss
                }
            else:
                patience_counter += 1
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{self.config.epochs} - "
                            f"Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}")
            
            if patience_counter >= self.config.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # Compute threshold from reconstruction errors on validation set
        self._compute_threshold(val_dataset)
        
        elapsed_time = time.time() - start_time
        
        # Update state
        self.state.is_trained = True
        self.state.training_samples_seen = len(time_series)
        self.state.current_threshold = self.config.threshold_percentile / 100.0
        self.state.training_loss_history = training_losses
        self.state.last_update_timestamp = datetime.utcnow().isoformat()
        
        # Save model if path specified
        if self.config.model_save_path:
            self.save_model(self.config.model_save_path)
        
        logger.info(f"Training completed in {elapsed_time:.2f}s")
        
        return {
            'success': True,
            'training_samples_seen': len(time_series),
            'epochs_completed': len(training_losses),
            'final_train_loss': training_losses[-1] if training_losses else None,
            'best_val_loss': best_val_loss,
            'threshold': self.state.current_threshold,
            'training_time_seconds': elapsed_time
        }
    
    def _compute_threshold(self, val_dataset: Dataset):
        """Compute anomaly threshold from validation set reconstruction errors."""
        if not HAS_TORCH or self.model is None:
            return
        
        device = self._setup_device()
        self.model.eval()
        
        reconstruction_errors = []
        
        with torch.no_grad():
            for batch_x, batch_y in val_dataset:
                if isinstance(batch_x, tuple):
                    batch_x, batch_y = batch_x
                
                batch_x = torch.tensor(batch_x, dtype=torch.float32).unsqueeze(0).to(device)
                reconstructed = self.model(batch_x)
                
                # MSE per sample
                errors = torch.mean((reconstructed - batch_x) ** 2, dim=(1, 2))
                reconstruction_errors.extend(errors.cpu().numpy())
        
        if reconstruction_errors:
            # Use percentile-based threshold
            threshold = float(np.percentile(reconstruction_errors, self.config.threshold_percentile))
            self.state.current_threshold = threshold
            self._reconstruction_errors = reconstruction_errors
            logger.info(f"Computed threshold: {threshold:.6f} (percentile {self.config.threshold_percentile})")
    
    def predict(self, time_series: np.ndarray) -> List[LSTM_AEPrediction]:
        """
        Generate anomaly predictions for a time series.
        
        Args:
            time_series: 1D array of time series values
        
        Returns:
            List of LSTM_AEPrediction objects
        """
        if not HAS_TORCH:
            logger.error("Cannot predict: PyTorch not available")
            return []
        
        if self.model is None:
            logger.warning("Model not trained, using mock predictions")
            return self._mock_predictions(time_series)
        
        time_series = np.asarray(time_series, dtype=np.float64).flatten()
        predictions = []
        
        device = self._setup_device()
        self.model.eval()
        
        # Normalize
        normalized = (time_series - self.scaler_mean) / self.scaler_std
        
        # Sliding window prediction
        for i in range(len(time_series) - self.config.sequence_length + 1):
            window = normalized[i:i + self.config.sequence_length]
            window_tensor = torch.tensor(
                window, dtype=torch.float32
            ).unsqueeze(0).unsqueeze(-1).to(device)  # (1, seq_len, 1)
            
            with torch.no_grad():
                reconstructed = self.model(window_tensor)
                reconstructed_np = reconstructed.cpu().numpy().flatten()
            
            # Compute reconstruction error (MSE)
            error = float(np.mean((window - reconstructed_np) ** 2))
            
            # Determine anomaly
            is_anomaly = error > self.state.current_threshold
            anomaly_score = error
            
            # Use middle value of window as timestamp
            timestamp_idx = i + self.config.sequence_length // 2
            timestamp = datetime.utcnow().isoformat()
            
            pred = LSTM_AEPrediction(
                timestamp=timestamp,
                input_value=float(time_series[timestamp_idx]),
                reconstructed_value=float(self.scaler_std * reconstructed_np[self.config.sequence_length // 2] + self.scaler_mean),
                reconstruction_error=error,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                model_state='trained' if self.state.is_trained else 'untrained'
            )
            predictions.append(pred)
        
        return predictions
    
    def _mock_predictions(self, time_series: np.ndarray) -> List[LSTM_AEPrediction]:
        """Generate mock predictions when model is not trained or PyTorch unavailable."""
        time_series = np.asarray(time_series, dtype=np.float64).flatten()
        predictions = []
        
        mock_threshold = float(np.std(time_series)) * 3.0
        
        for i, val in enumerate(time_series):
            mock_error = abs(val - np.mean(time_series))
            is_anomaly = mock_error > mock_threshold
            
            timestamp = datetime.utcnow().isoformat()
            pred = LSTM_AEPrediction(
                timestamp=timestamp,
                input_value=float(val),
                reconstructed_value=float(val),
                reconstruction_error=mock_error,
                is_anomaly=is_anomaly,
                anomaly_score=mock_error,
                model_state='untrained'
            )
            predictions.append(pred)
        
        return predictions
    
    def save_model(self, path: str):
        """Save trained model to disk."""
        if not HAS_TORCH or self.model is None:
            logger.warning("Cannot save: model not available")
            return
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        save_data = {
            'config': asdict(self.config),
            'state': self.state.to_dict(),
            'model_state_dict': self.model.state_dict(),
            'scaler_mean': self.scaler_mean,
            'scaler_std': self.scaler_std,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        torch.save(save_data, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained model from disk."""
        if not HAS_TORCH:
            logger.error("Cannot load: PyTorch not available")
            return False
        
        path = Path(path)
        if not path.exists():
            logger.error(f"Model file not found: {path}")
            return False
        
        try:
            save_data = torch.load(path, map_location=self._setup_device())
            
            self.config = LSTM_AEConfig(**save_data['config'])
            self.state = LSTM_AEState.from_dict(save_data['state'])
            self.scaler_mean = save_data['scaler_mean']
            self.scaler_std = save_data['scaler_std']
            
            self.model = LSTM_AE(
                input_size=self.config.input_size,
                hidden_size=self.config.hidden_size,
                num_layers=self.config.num_layers,
                dropout=self.config.dropout
            ).to(self._setup_device())
            self.model.load_state_dict(save_data['model_state_dict'])
            
            self.state.is_trained = True
            logger.info(f"Model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get baseline metrics and statistics."""
        return {
            'model_type': 'LSTM_Autoencoder',
            'is_trained': self.state.is_trained,
            'training_samples_seen': self.state.training_samples_seen,
            'current_threshold': self.state.current_threshold,
            'config': asdict(self.config),
            'reconstruction_error_stats': {
                'mean': float(np.mean(self._reconstruction_errors)) if self._reconstruction_errors else 0.0,
                'std': float(np.std(self._reconstruction_errors)) if self._reconstruction_errors else 0.0,
                'min': float(np.min(self._reconstruction_errors)) if self._reconstruction_errors else 0.0,
                'max': float(np.max(self._reconstruction_errors)) if self._reconstruction_errors else 0.0
            }
        }


def create_baseline(config: Optional[LSTM_AEConfig] = None) -> LSTM_AEBaseline:
    """
    Factory function to create LSTM Autoencoder baseline.
    
    Args:
        config: Configuration object. If None, uses defaults.
    
    Returns:
        Configured LSTM_AEBaseline instance
    """
    return LSTM_AEBaseline(config)


def main():
    """
    Main entry point for standalone execution.
    
    This function:
    1. Generates synthetic time series data with known anomalies
    2. Trains the LSTM Autoencoder
    3. Evaluates on test data
    4. Outputs results to JSON
    """
    if not HAS_TORCH:
        print("ERROR: PyTorch not available. Install with: pip install torch")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("LSTM Autoencoder Baseline - Standalone Execution")
    logger.info("=" * 60)
    
    # Generate synthetic data
    logger.info("Generating synthetic time series with anomalies...")
    np.random.seed(42)
    
    # Normal signal: sine wave + noise
    n_normal = 1000
    t = np.linspace(0, 4 * np.pi, n_normal)
    normal_signal = np.sin(t) + 0.1 * np.random.randn(n_normal)
    
    # Inject anomalies (5% of points)
    n_anomalies = int(0.05 * n_normal)
    anomaly_indices = np.random.choice(n_normal, n_anomalies, replace=False)
    normal_signal[anomaly_indices] += 3.0 * np.random.randn(n_anomalies)
    
    # Split into train/test (80/20)
    split_idx = int(0.8 * n_normal)
    train_data = normal_signal[:split_idx]
    test_data = normal_signal[split_idx:]
    
    # Create ground truth labels
    train_labels = np.zeros(len(train_data), dtype=int)
    train_labels[anomaly_indices[anomaly_indices < split_idx]] = 1
    
    test_labels = np.zeros(len(test_data), dtype=int)
    test_anomaly_indices = anomaly_indices[anomaly_indices >= split_idx] - split_idx
    test_labels[test_anomaly_indices] = 1
    
    logger.info(f"Training data: {len(train_data)} samples")
    logger.info(f"Test data: {len(test_data)} samples")
    logger.info(f"Anomalies in train: {np.sum(train_labels)}")
    logger.info(f"Anomalies in test: {np.sum(test_labels)}")
    
    # Create and train model
    config = LSTM_AEConfig(
        input_size=1,
        hidden_size=32,
        num_layers=2,
        dropout=0.2,
        sequence_length=20,
        learning_rate=0.001,
        batch_size=32,
        epochs=30,
        early_stopping_patience=5,
        threshold_percentile=95.0,
        seed=42
    )
    
    baseline = create_baseline(config)
    
    logger.info("Training LSTM Autoencoder...")
    train_results = baseline.train(train_data, train_labels)
    
    if not train_results['success']:
        logger.error(f"Training failed: {train_results.get('error', 'Unknown error')}")
        sys.exit(1)
    
    logger.info(f"Training completed: {train_results}")
    
    # Evaluate on test data
    logger.info("Evaluating on test data...")
    predictions = baseline.predict(test_data)
    
    if not predictions:
        logger.error("No predictions generated")
        sys.exit(1)
    
    # Compute metrics
    pred_labels = np.array([p.is_anomaly for p in predictions])
    true_labels = test_labels[:len(predictions)]
    
    tp = np.sum((pred_labels == 1) & (true_labels == 1))
    fp = np.sum((pred_labels == 1) & (true_labels == 0))
    fn = np.sum((pred_labels == 0) & (true_labels == 1))
    
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)
    
    logger.info(f"Test Results:")
    logger.info(f"  Precision: {precision:.4f}")
    logger.info(f"  Recall: {recall:.4f}")
    logger.info(f"  F1-Score: {f1:.4f}")
    
    # Save results
    output = {
        'baseline_type': 'LSTM_Autoencoder',
        'config': asdict(config),
        'training_results': train_results,
        'test_metrics': {
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'true_positives': int(tp),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'total_test_samples': len(test_data),
            'predicted_anomalies': int(np.sum(pred_labels)),
            'true_anomalies': int(np.sum(true_labels))
        },
        'model_state': baseline.get_metrics(),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    output_path = Path('data/processed/lstm_ae_baseline_results.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")
    logger.info("=" * 60)
    logger.info("LSTM Autoencoder Baseline execution complete")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
