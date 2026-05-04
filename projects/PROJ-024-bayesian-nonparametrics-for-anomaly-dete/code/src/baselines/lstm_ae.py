"""
LSTM Autoencoder Baseline for Time Series Anomaly Detection

This module implements a sequence-to-sequence LSTM autoencoder that
reconstructs time series windows and uses reconstruction error as
the anomaly score. Matches the API surface of other baselines (ARIMA,
MovingAverage) for consistent evaluation.

API Surface (per spec.md):
- LSTMConfig: Configuration dataclass for hyperparameters
- LSTMPrediction: Prediction output with reconstruction and score
- LSTMState: Model state for serialization
- LSTMAutoencoder: Neural network model
- LSTMBaseline: High-level baseline interface
- create_baseline: Factory function
- main: Entry point for script execution
"""
import os
import sys
import json
import logging
import numpy as np
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Union
import warnings
warnings.filterwarnings('ignore')

# Try to import torch, fall back gracefully if not available
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - LSTM baseline will use numpy fallback")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LSTMConfig:
    """Configuration for LSTM Autoencoder baseline."""
    # Model architecture
    hidden_size: int = 64
    num_layers: int = 2
    sequence_length: int = 10  # Window size for sequences
    dropout: float = 0.1
    
    # Training parameters
    epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.001
    early_stopping_patience: int = 10
    
    # Anomaly detection
    anomaly_threshold_percentile: float = 95.0  # Use reconstruction error percentile
    min_anomaly_score: float = 0.0
    max_anomaly_score: float = 1.0
    
    # Data preprocessing
    normalize: bool = True
    normalize_method: str = 'zscore'  # 'zscore', 'minmax', 'robust'
    
    # Random seed for reproducibility
    random_seed: int = 42
    
    # Paths
    model_path: Optional[str] = None
    results_path: str = 'data/processed/results/'
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.hidden_size < 16:
            raise ValueError("hidden_size must be at least 16")
        if self.num_layers < 1:
            raise ValueError("num_layers must be at least 1")
        if self.sequence_length < 2:
            raise ValueError("sequence_length must be at least 2")
        if not 0.0 < self.learning_rate < 1.0:
            raise ValueError("learning_rate must be between 0 and 1")
        if not 0 < self.epochs:
            raise ValueError("epochs must be positive")

@dataclass
class LSTMPrediction:
    """Prediction output from LSTM Autoencoder."""
    timestamp: int  # Index in original time series
    value: float  # Original value
    reconstructed_value: float  # Reconstructed value
    anomaly_score: float  # Reconstruction error (normalized)
    is_anomaly: bool  # Binary anomaly flag
    reconstruction_error: float  # Raw reconstruction error (MSE)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

@dataclass
class LSTMState:
    """Model state for serialization and checkpointing."""
    config_dict: Dict[str, Any]
    training_history: List[Dict[str, float]]
    threshold: float
    normalization_params: Dict[str, float]
    model_path: Optional[str]
    created_at: str
    input_dim: int
    total_samples: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

class SequenceDataset(Dataset):
    """PyTorch Dataset for time series sequences."""
    
    def __init__(self, sequences: np.ndarray, targets: Optional[np.ndarray] = None):
        """
        Args:
            sequences: Array of shape (n_samples, sequence_length, features)
            targets: Optional targets for reconstruction (same shape as sequences)
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")
        
        self.sequences = torch.FloatTensor(sequences)
        if targets is not None:
            self.targets = torch.FloatTensor(targets)
        else:
            self.targets = self.sequences
        
        assert self.sequences.shape[0] == self.targets.shape[0], \
            "Sequences and targets must have same number of samples"
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.sequences[idx], self.targets[idx]

class LSTMAutoencoder(nn.Module):
    """
    LSTM Autoencoder for time series reconstruction.
    
    Architecture:
    - Encoder: LSTM layers that compress input sequence to hidden state
    - Decoder: LSTM layers that reconstruct sequence from hidden state
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Encoder: Compress sequence to hidden state
        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        
        # Decoder: Reconstruct sequence from hidden state
        self.decoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        
        # Output projection
        self.output_proj = nn.Linear(hidden_size, input_dim)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights for better convergence."""
        for name, param in self.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.zeros_(param)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_dim)
        
        Returns:
            Reconstructed tensor of shape (batch_size, sequence_length, input_dim)
        """
        # Encode: (batch, seq, input_dim) -> (batch, seq, hidden)
        # We only use the last hidden state for the bottleneck
        _, (hidden, _) = self.encoder(x)
        
        # Decode: Create sequence from hidden state
        # Expand hidden state to full sequence length
        batch_size = x.size(0)
        seq_length = x.size(1)
        
        # Use hidden state as initial state for decoder
        # Repeat the last hidden state for each timestep
        decoder_input = hidden[-1].unsqueeze(1).expand(-1, seq_length, -1)
        
        # Actually, better approach: use encoder output for decoder input
        # Re-run encoder to get full sequence output
        encoder_output, (hidden, _) = self.encoder(x)
        
        # Decoder takes encoder output and reconstructs
        decoder_output, _ = self.decoder(encoder_output, (hidden, _))
        
        # Project to input dimension
        reconstructed = self.output_proj(decoder_output)
        
        return reconstructed
    
    def get_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """
        Compute mean squared error between input and reconstruction.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_dim)
        
        Returns:
            MSE per sample: (batch_size,)
        """
        reconstructed = self.forward(x)
        mse = torch.mean((x - reconstructed) ** 2, dim=(1, 2))
        return mse

class LSTMBaseline:
    """
    High-level LSTM Autoencoder baseline interface.
    
    Matches the API surface of ARIMABaseline and MovingAverageBaseline
    for consistent evaluation across baselines.
    """
    
    def __init__(self, config: Optional[LSTMConfig] = None):
        """
        Args:
            config: LSTMConfig instance or None to use defaults
        """
        self.config = config or LSTMConfig()
        self.model: Optional[LSTMAutoencoder] = None
        self.state: Optional[LSTMState] = None
        self.is_fitted = False
        self.normalization_params: Dict[str, float] = {}
        self.threshold: float = 0.0
        
        # Set random seed for reproducibility
        if TORCH_AVAILABLE:
            torch.manual_seed(self.config.random_seed)
            np.random.seed(self.config.random_seed)
        
        logger.info(f"Initialized LSTMBaseline with config: hidden_size={self.config.hidden_size}, "
                   f"sequence_length={self.config.sequence_length}, epochs={self.config.epochs}")
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """
        Normalize time series data.
        
        Args:
            data: 1D array of shape (n_samples,)
        
        Returns:
            Normalized array and normalization parameters
        """
        if not self.config.normalize:
            return data, {}
        
        if self.config.normalize_method == 'zscore':
            mean = np.mean(data)
            std = np.std(data)
            if std < 1e-10:
                std = 1.0
            normalized = (data - mean) / std
            params = {'mean': float(mean), 'std': float(std), 'method': 'zscore'}
        elif self.config.normalize_method == 'minmax':
            min_val = np.min(data)
            max_val = np.max(data)
            if max_val - min_val < 1e-10:
                max_val = min_val + 1.0
            normalized = (data - min_val) / (max_val - min_val)
            params = {'min': float(min_val), 'max': float(max_val), 'method': 'minmax'}
        elif self.config.normalize_method == 'robust':
            median = np.median(data)
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            if iqr < 1e-10:
                iqr = 1.0
            normalized = (data - median) / iqr
            params = {'median': float(median), 'iqr': float(iqr), 'method': 'robust'}
        else:
            raise ValueError(f"Unknown normalization method: {self.config.normalize_method}")
        
        return normalized, params
    
    def _denormalize(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Denormalize data using stored parameters."""
        if self.config.normalize_method == 'zscore':
            return data * params['std'] + params['mean']
        elif self.config.normalize_method == 'minmax':
            return data * (params['max'] - params['min']) + params['min']
        elif self.config.normalize_method == 'robust':
            return data * params['iqr'] + params['median']
        return data
    
    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """
        Create sliding window sequences from time series.
        
        Args:
            data: 1D array of shape (n_samples,)
        
        Returns:
            Array of shape (n_samples - sequence_length + 1, sequence_length, 1)
        """
        seq_len = self.config.sequence_length
        if len(data) < seq_len:
            raise ValueError(f"Data length ({len(data)}) < sequence_length ({seq_len})")
        
        sequences = []
        for i in range(len(data) - seq_len + 1):
            sequences.append(data[i:i + seq_len].reshape(-1, 1))
        
        return np.array(sequences)
    
    def fit(self, data: np.ndarray) -> 'LSTMBaseline':
        """
        Train the LSTM Autoencoder on time series data.
        
        Args:
            data: 1D array of shape (n_samples,) representing the time series
        
        Returns:
            self for method chaining
        """
        if not TORCH_AVAILABLE:
            logger.error("PyTorch not available - cannot train LSTM model")
            raise RuntimeError("PyTorch not installed. Install with: pip install torch")
        
        logger.info(f"Training LSTM Autoencoder on {len(data)} samples...")
        
        # Normalize data
        normalized_data, norm_params = self._normalize(data)
        self.normalization_params = norm_params
        
        # Create sequences
        sequences = self._create_sequences(normalized_data)
        
        # Create dataset and dataloader
        dataset = SequenceDataset(sequences)
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            drop_last=True
        )
        
        # Initialize model
        self.model = LSTMAutoencoder(
            input_dim=1,  # Single feature
            hidden_size=self.config.hidden_size,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout
        )
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.config.learning_rate
        )
        
        # Training loop
        training_history = []
        best_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            num_batches = 0
            
            for batch_x, batch_y in dataloader:
                optimizer.zero_grad()
                reconstructed = self.model(batch_x)
                loss = criterion(reconstructed, batch_y)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / num_batches
            training_history.append({'epoch': epoch, 'loss': float(avg_loss)})
            
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
                # Save best model state
                best_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}/{self.config.epochs}, Loss: {avg_loss:.6f}")
            
            # Early stopping
            if patience_counter >= self.config.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch}")
                self.model.load_state_dict(best_state)
                break
        
        # Calculate threshold based on training reconstruction errors
        self.model.eval()
        with torch.no_grad():
            train_errors = self.model.get_reconstruction_error(
                torch.FloatTensor(sequences)
            ).numpy()
        
        self.threshold = np.percentile(
            train_errors,
            self.config.anomaly_threshold_percentile
        )
        
        # Create state
        self.state = LSTMState(
            config_dict=asdict(self.config),
            training_history=training_history,
            threshold=float(self.threshold),
            normalization_params=self.normalization_params,
            model_path=self.config.model_path,
            created_at=datetime.now().isoformat(),
            input_dim=1,
            total_samples=len(data)
        )
        
        self.is_fitted = True
        logger.info(f"LSTM Autoencoder trained successfully. Threshold: {self.threshold:.6f}")
        
        return self
    
    def predict(self, data: np.ndarray) -> List[LSTMPrediction]:
        """
        Predict anomaly scores for time series data.
        
        Args:
            data: 1D array of shape (n_samples,) representing the time series
        
        Returns:
            List of LSTMPrediction objects for each time step
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction. Call fit() first.")
        
        if not TORCH_AVAILABLE:
            logger.error("PyTorch not available - cannot make predictions")
            raise RuntimeError("PyTorch not installed. Install with: pip install torch")
        
        logger.info(f"Making predictions on {len(data)} samples...")
        
        # Normalize data using stored parameters
        normalized_data, _ = self._normalize(data)
        
        # Create sequences
        sequences = self._create_sequences(normalized_data)
        
        # Create dataset
        dataset = SequenceDataset(sequences)
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            drop_last=False
        )
        
        # Get reconstruction errors
        self.model.eval()
        all_errors = []
        
        with torch.no_grad():
            for batch_x, _ in dataloader:
                errors = self.model.get_reconstruction_error(batch_x)
                all_errors.extend(errors.numpy().tolist())
        
        # Convert to numpy array
        all_errors = np.array(all_errors)
        
        # Normalize scores to [0, 1] range
        if len(all_errors) > 0:
            max_error = np.max(all_errors)
            if max_error > 0:
                normalized_scores = np.clip(all_errors / max_error, 0.0, 1.0)
            else:
                normalized_scores = np.zeros_like(all_errors)
        else:
            normalized_scores = np.array([])
        
        # Create predictions
        # Note: predictions are aligned with the END of each sequence window
        predictions = []
        for i, (error, score) in enumerate(zip(all_errors, normalized_scores)):
            # The prediction corresponds to the last timestep of the sequence
            seq_end_idx = i + self.config.sequence_length - 1
            if seq_end_idx < len(data):
                predictions.append(LSTMPrediction(
                    timestamp=seq_end_idx,
                    value=float(data[seq_end_idx]),
                    reconstructed_value=float(self._denormalize(
                        np.array([normalized_data[seq_end_idx]]),
                        self.normalization_params
                    )[0]),
                    anomaly_score=float(np.clip(score, self.config.min_anomaly_score, self.config.max_anomaly_score)),
                    is_anomaly=bool(error > self.threshold),
                    reconstruction_error=float(error)
                ))
        
        logger.info(f"Generated {len(predictions)} predictions. Anomalies detected: {sum(p.is_anomaly for p in predictions)}")
        
        return predictions
    
    def compute_anomaly_scores(self, data: np.ndarray) -> np.ndarray:
        """
        Compute anomaly scores (reconstruction errors) for time series.
        
        Args:
            data: 1D array of shape (n_samples,)
        
        Returns:
            Array of anomaly scores aligned with input data
            (first sequence_length-1 elements will be NaN)
        """
        predictions = self.predict(data)
        scores = np.full(len(data), np.nan)
        
        for pred in predictions:
            scores[pred.timestamp] = pred.anomaly_score
        
        return scores
    
    def save_checkpoint(self, path: Optional[str] = None) -> None:
        """
        Save model checkpoint.
        
        Args:
            path: Optional path to save checkpoint. Uses config.model_path if None.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available - cannot save checkpoint")
        
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before saving checkpoint")
        
        save_path = path or self.config.model_path
        if save_path is None:
            raise ValueError("No path provided for checkpoint")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model state
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': asdict(self.config),
            'state': self.state.to_dict() if self.state else None,
            'normalization_params': self.normalization_params,
            'threshold': self.threshold,
        }, save_path)
        
        logger.info(f"Checkpoint saved to {save_path}")
    
    @classmethod
    def load_checkpoint(cls, path: str) -> 'LSTMBaseline':
        """
        Load model from checkpoint.
        
        Args:
            path: Path to checkpoint file
        
        Returns:
            LSTMBaseline instance with loaded model
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available - cannot load checkpoint")
        
        checkpoint = torch.load(path, map_location='cpu')
        
        # Create model with loaded config
        config = LSTMConfig(**checkpoint['config'])
        model = cls(config)
        
        # Load model state
        model.model = LSTMAutoencoder(
            input_dim=1,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout
        )
        model.model.load_state_dict(checkpoint['model_state_dict'])
        
        # Load other state
        model.normalization_params = checkpoint['normalization_params']
        model.threshold = checkpoint['threshold']
        model.is_fitted = True
        
        if checkpoint.get('state'):
            model.state = LSTMState(**checkpoint['state'])
        
        logger.info(f"Checkpoint loaded from {path}")
        
        return model
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get summary of model architecture and training status.
        
        Returns:
            Dictionary with model information
        """
        if not self.is_fitted:
            return {'is_fitted': False}
        
        summary = {
            'is_fitted': True,
            'config': asdict(self.config),
            'threshold': self.threshold,
            'normalization_params': self.normalization_params,
            'training_epochs': len(self.state.training_history) if self.state else 0,
            'total_samples': self.state.total_samples if self.state else 0,
        }
        
        if self.model:
            # Count parameters
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            summary['total_parameters'] = total_params
            summary['trainable_parameters'] = trainable_params
        
        return summary
    
    def evaluate(
        self,
        data: np.ndarray,
        ground_truth: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Evaluate model performance on data.
        
        Args:
            data: 1D array of time series values
            ground_truth: Optional binary array of ground truth anomalies
        
        Returns:
            Dictionary with evaluation metrics
        """
        predictions = self.predict(data)
        
        # Extract scores and predictions
        scores = np.array([p.anomaly_score for p in predictions])
        binary_preds = np.array([p.is_anomaly for p in predictions])
        timestamps = np.array([p.timestamp for p in predictions])
        
        results = {
            'n_predictions': len(predictions),
            'n_anomalies_detected': int(np.sum(binary_preds)),
            'anomaly_rate': float(np.mean(binary_preds)),
            'threshold': self.threshold,
            'min_score': float(np.min(scores)) if len(scores) > 0 else 0.0,
            'max_score': float(np.max(scores)) if len(scores) > 0 else 0.0,
            'mean_score': float(np.mean(scores)) if len(scores) > 0 else 0.0,
            'std_score': float(np.std(scores)) if len(scores) > 0 else 0.0,
        }
        
        # Compute metrics against ground truth if available
        if ground_truth is not None:
            # Align ground truth with predictions
            gt_aligned = np.full(len(data), False)
            for pred in predictions:
                if pred.timestamp < len(ground_truth):
                    gt_aligned[pred.timestamp] = ground_truth[pred.timestamp]
            
            # Extract aligned predictions
            binary_preds_aligned = np.array([
                pred.is_anomaly for pred in predictions
                if pred.timestamp < len(ground_truth)
            ])
            gt_aligned_preds = np.array([
                ground_truth[pred.timestamp] for pred in predictions
                if pred.timestamp < len(ground_truth)
            ])
            
            if len(binary_preds_aligned) > 0:
                tp = np.sum((binary_preds_aligned == 1) & (gt_aligned_preds == 1))
                fp = np.sum((binary_preds_aligned == 1) & (gt_aligned_preds == 0))
                fn = np.sum((binary_preds_aligned == 0) & (gt_aligned_preds == 1))
                tn = np.sum((binary_preds_aligned == 0) & (gt_aligned_preds == 0))
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
                
                results.update({
                    'true_positives': int(tp),
                    'false_positives': int(fp),
                    'true_negatives': int(tn),
                    'false_negatives': int(fn),
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1_score': float(f1),
                })
        
        return results
    
    def __repr__(self) -> str:
        return f"LSTMBaseline(config={self.config})"

def create_baseline(config: Optional[LSTMConfig] = None) -> LSTMBaseline:
    """
    Factory function to create LSTM baseline instance.
    
    Args:
        config: Optional LSTMConfig instance
    
    Returns:
        LSTMBaseline instance
    """
    return LSTMBaseline(config=config)

def main():
    """
    Main entry point for script execution.
    
    This function:
    1. Loads or generates synthetic time series data
    2. Trains the LSTM Autoencoder
    3. Computes anomaly scores
    4. Saves results to data/processed/results/
    """
    logger.info("=" * 60)
    logger.info("LSTM Autoencoder Baseline - Script Execution")
    logger.info("=" * 60)
    
    # Create results directory
    results_dir = Path('data/processed/results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic test data with known anomalies
    logger.info("Generating synthetic test data...")
    np.random.seed(42)
    n_samples = 1000
    base_signal = np.sin(np.linspace(0, 10 * np.pi, n_samples))
    noise = np.random.normal(0, 0.1, n_samples)
    data = base_signal + noise
    
    # Inject some anomalies (spikes)
    anomaly_indices = [200, 400, 600, 800]
    for idx in anomaly_indices:
        if idx < len(data):
            data[idx] += 3.0  # Large spike
    
    logger.info(f"Generated {len(data)} samples with anomalies at {anomaly_indices}")
    
    # Create and train model
    config = LSTMConfig(
        hidden_size=32,
        num_layers=2,
        sequence_length=10,
        epochs=20,
        batch_size=32,
        learning_rate=0.001,
        normalize=True,
        normalize_method='zscore',
        random_seed=42
    )
    
    baseline = create_baseline(config)
    baseline.fit(data)
    
    # Make predictions
    predictions = baseline.predict(data)
    
    # Evaluate
    ground_truth = np.zeros(len(data), dtype=bool)
    for idx in anomaly_indices:
        if idx < len(data):
            ground_truth[idx] = True
    
    evaluation = baseline.evaluate(data, ground_truth)
    
    # Save results
    results = {
        'model_summary': baseline.get_model_summary(),
        'evaluation': evaluation,
        'config': asdict(config),
        'n_samples': len(data),
        'n_anomalies_injected': len(anomaly_indices),
        'timestamp': datetime.now().isoformat(),
    }
    
    results_path = results_dir / 'lstm_ae_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save predictions
    predictions_path = results_dir / 'lstm_ae_predictions.json'
    with open(predictions_path, 'w') as f:
        json.dump([p.to_dict() for p in predictions], f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    logger.info(f"Predictions saved to {predictions_path}")
    logger.info(f"Evaluation metrics: {json.dumps(evaluation, indent=2)}")
    
    # Save checkpoint
    checkpoint_path = results_dir / 'lstm_ae_checkpoint.pth'
    baseline.save_checkpoint(str(checkpoint_path))
    
    logger.info("=" * 60)
    logger.info("LSTM Autoencoder Baseline - Execution Complete")
    logger.info("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
