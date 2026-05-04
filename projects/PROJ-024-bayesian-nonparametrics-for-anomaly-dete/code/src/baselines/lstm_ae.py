"""
LSTM Autoencoder Baseline for Time Series Anomaly Detection.

This module implements an LSTM-based autoencoder for anomaly detection
in univariate time series data. The model learns to reconstruct normal
patterns and flags points with high reconstruction error as anomalies.

Follows the same interface pattern as ARIMABaseline and MovingAverageBaseline.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import sys
import json
import logging
import os

# Try to import torch, fall back gracefully if not available
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
  TORCH_AVAILABLE = False
  logging.warning("PyTorch not available. LSTM-AE baseline will be in stub mode.")

from src.models.time_series import TimeSeries
from src.utils.streaming import StreamingObservation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LSTMConfig:
    """Configuration for LSTM Autoencoder."""
    input_size: int = 1
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    sequence_length: int = 50
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    patience: int = 10
    threshold_percentile: float = 95.0
    random_seed: int = 42
    device: str = "cpu"
    checkpoint_path: Optional[str] = None

@dataclass
class LSTMPrediction:
    """Prediction output from LSTM-AE baseline."""
    timestamp: datetime
    value: float
    reconstruction: float
    anomaly_score: float
    is_anomaly: bool
    model_version: str = "lstm-ae-v1"

@dataclass
class LSTMState:
    """State tracking for LSTM-AE training."""
    training_loss_history: List[float] = field(default_factory=list)
    val_loss_history: List[float] = field(default_factory=list)
    best_val_loss: float = float('inf')
    epochs_trained: int = 0
    early_stopping_triggered: bool = False
    threshold_value: float = 0.0
    model_trained: bool = False
    trained_at: Optional[str] = None

class LSTMEncoder(nn.Module):
    """LSTM Encoder for Autoencoder."""

    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

    def forward(self, x):
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_size)
        Returns:
            encoded: Hidden state of shape (batch_size, hidden_size)
        """
        # x shape: (batch, seq_len, input_size)
        output, (hidden, cell) = self.lstm(x)
        # Return the last hidden state
        return hidden[-1]  # (batch, hidden_size)

class LSTMDecoder(nn.Module):
    """LSTM Decoder for Autoencoder."""

    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = input_size

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        self.fc = nn.Linear(hidden_size, input_size)

    def forward(self, encoded, seq_len: int):
        """
        Args:
            encoded: Encoded tensor of shape (batch_size, hidden_size)
            seq_len: Desired output sequence length
        Returns:
            decoded: Reconstructed tensor of shape (batch_size, seq_len, input_size)
        """
        batch_size = encoded.shape[0]

        # Initialize decoder input with zeros
        decoder_input = torch.zeros(batch_size, 1, self.output_size, device=encoded.device)

        # Use encoded state as initial hidden state
        hidden = encoded.unsqueeze(0)  # (1, batch, hidden_size)
        cell = torch.zeros_like(hidden)  # (1, batch, hidden_size)

        outputs = []

        for _ in range(seq_len):
            output, (hidden, cell) = self.lstm(decoder_input, (hidden, cell))
            pred = self.fc(output.squeeze(1))  # (batch, output_size)
            outputs.append(pred)
            decoder_input = pred.unsqueeze(1)  # (batch, 1, output_size)

        # Stack all outputs
        decoded = torch.stack(outputs, dim=1)  # (batch, seq_len, output_size)
        return decoded

class LSTMAutoencoder(nn.Module):
    """LSTM Autoencoder for time series reconstruction."""

    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float):
        super().__init__()
        self.encoder = LSTMEncoder(input_size, hidden_size, num_layers, dropout)
        self.decoder = LSTMDecoder(input_size, hidden_size, num_layers, dropout)
        self.hidden_size = hidden_size
        self.num_layers = num_layers

    def forward(self, x):
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_size)
        Returns:
            reconstructed: Reconstructed tensor of same shape as input
        """
        encoded = self.encoder(x)
        seq_len = x.shape[1]
        reconstructed = self.decoder(encoded, seq_len)
        return reconstructed

class LSTMAEBaseline:
    """
    LSTM Autoencoder Baseline for Anomaly Detection.

    This baseline uses an LSTM autoencoder to learn normal patterns in
    time series data. Anomalies are detected based on reconstruction error.

    Interface matches ARIMABaseline and MovingAverageBaseline for consistency.
    """

    def __init__(self, config: Optional[LSTMConfig] = None):
        """
        Initialize the LSTM-AE baseline.

        Args:
            config: LSTMConfig with model hyperparameters. If None, uses defaults.
        """
        self.config = config or LSTMConfig()
        self.state = LSTMState()
        self.model: Optional[LSTMAutoencoder] = None
        self.scaler_mean: float = 0.0
        self.scaler_std: float = 1.0

        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. LSTM-AE will run in stub mode.")

    def _init_model(self):
        """Initialize the LSTM autoencoder model."""
        if not TORCH_AVAILABLE:
            return

        self.model = LSTMAutoencoder(
            input_size=self.config.input_size,
            hidden_size=self.config.hidden_size,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout
        )

        # Move to device
        device = torch.device(self.config.device)
        self.model.to(device)

        # Initialize weights
        for p in self.model.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

        logger.info(f"Initialized LSTM-AE model with {self._count_parameters()} parameters")

    def _count_parameters(self) -> int:
        """Count total trainable parameters in the model."""
        if self.model is None:
            return 0
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)

    def _prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare time series data for LSTM training.

        Args:
            data: 1D array of time series values

        Returns:
            X: Sequences of shape (num_samples, seq_len, 1)
            y: Same as X for autoencoder (self-supervised)
        """
        seq_len = self.config.sequence_length
        if len(data) < seq_len:
            raise ValueError(f"Data length {len(data)} < sequence_length {seq_len}")

        sequences = []
        for i in range(len(data) - seq_len + 1):
            sequences.append(data[i:i+seq_len])

        X = np.array(sequences).reshape(-1, seq_len, 1)
        y = X.copy()  # Autoencoder learns to reconstruct

        return X, y

    def _normalize_data(self, data: np.ndarray) -> np.ndarray:
        """Normalize data for training."""
        self.scaler_mean = float(np.mean(data))
        self.scaler_std = float(np.std(data))
        if self.scaler_std < 1e-8:
            self.scaler_std = 1.0
        return (data - self.scaler_mean) / self.scaler_std

    def _denormalize_data(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data back to original scale."""
        return data * self.scaler_std + self.scaler_mean

    def train(self, time_series: TimeSeries, val_split: float = 0.2) -> LSTMState:
        """
        Train the LSTM-AE model on the provided time series.

        Args:
            time_series: TimeSeries object with values and timestamps
            val_split: Fraction of data to use for validation

        Returns:
            LSTMState with training history and status
        """
        if not TORCH_AVAILABLE:
            logger.error("Cannot train: PyTorch not available")
            return self.state

        if self.model is None:
            self._init_model()

        # Extract and normalize data
        values = np.array(time_series.values, dtype=np.float32)
        values_norm = self._normalize_data(values)

        # Prepare sequences
        X, y = self._prepare_sequences(values_norm)

        # Split into train/val
        split_idx = int(len(X) * (1 - val_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Create DataLoaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val),
            torch.FloatTensor(y_val)
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False
        )

        # Setup optimizer and loss
        device = torch.device(self.config.device)
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()

        # Training loop with early stopping
        patience_counter = 0
        best_val_loss = float('inf')
        best_model_state = None

        logger.info(f"Starting training for {self.config.epochs} epochs...")

        for epoch in range(self.config.epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)

                optimizer.zero_grad()
                output = self.model(batch_x)
                loss = criterion(output, batch_y)
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                optimizer.step()
                train_loss += loss.item()

            train_loss /= len(train_loader)
            self.state.training_loss_history.append(train_loss)

            # Validation phase
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                    output = self.model(batch_x)
                    loss = criterion(output, batch_y)
                    val_loss += loss.item()

            val_loss /= len(val_loader)
            self.state.val_loss_history.append(val_loss)

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
                self.state.best_val_loss = best_val_loss
            else:
                patience_counter += 1

            self.state.epochs_trained = epoch + 1

            if patience_counter >= self.config.patience:
                self.state.early_stopping_triggered = True
                logger.info(f"Early stopping at epoch {epoch + 1}")
                break

            if (epoch + 1) % 10 == 0 or epoch == 0:
                logger.info(f"Epoch {epoch + 1}/{self.config.epochs} - "
                            f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

        # Load best model
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)

        # Calculate threshold for anomaly detection
        self._calculate_threshold(X_val, y_val)

        self.state.model_trained = True
        self.state.trained_at = datetime.now().isoformat()

        logger.info(f"Training complete. Final val loss: {self.state.best_val_loss:.6f}")
        return self.state

    def _calculate_threshold(self, X_val: np.ndarray, y_val: np.ndarray):
        """Calculate anomaly threshold based on validation reconstruction errors."""
        if not TORCH_AVAILABLE or self.model is None:
            self.state.threshold_value = 0.0
            return

        device = torch.device(self.config.device)
        self.model.eval()

        # Calculate reconstruction errors on validation set
        errors = []
        with torch.no_grad():
            X_val_tensor = torch.FloatTensor(X_val).to(device)
            reconstructed = self.model(X_val_tensor)

            # MSE per sample
            mse = torch.mean((reconstructed - X_val_tensor) ** 2, dim=(1, 2))
            errors = mse.cpu().numpy()

        # Set threshold at specified percentile
        self.state.threshold_value = float(np.percentile(errors, self.config.threshold_percentile))
        logger.info(f"Anomaly threshold set to: {self.state.threshold_value:.6f} "
                   f"(at {self.config.threshold_percentile}th percentile)")

    def predict(self, time_series: TimeSeries) -> List[LSTMPrediction]:
        """
        Generate anomaly predictions for a time series.

        Args:
            time_series: TimeSeries object to score

        Returns:
            List of LSTMPrediction objects for each point
        """
        if not TORCH_AVAILABLE:
            logger.error("Cannot predict: PyTorch not available")
            return []

        if not self.state.model_trained:
            logger.warning("Model not trained. Training with available data first.")
            self.train(time_series)

        if self.model is None:
            return []

        values = np.array(time_series.values, dtype=np.float32)
        values_norm = self._normalize_data(values)

        device = torch.device(self.config.device)
        self.model.eval()

        predictions = []
        timestamps = time_series.timestamps

        # Use sliding window for predictions
        seq_len = self.config.sequence_length

        for i in range(seq_len - 1, len(values)):
            # Extract sequence ending at current point
            sequence = values_norm[i - seq_len + 1:i + 1]
            sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(device)

            with torch.no_grad():
                reconstructed = self.model(sequence_tensor)
                reconstruction = reconstructed.squeeze().cpu().numpy()

            # Calculate reconstruction error for the last point
            target = values_norm[i]
            recon_target = reconstruction[-1]
            error = (target - recon_target) ** 2

            is_anomaly = error > self.state.threshold_value

            pred = LSTMPrediction(
                timestamp=timestamps[i] if i < len(timestamps) else datetime.now(),
                value=float(values[i]),
                reconstruction=float(recon_target),
                anomaly_score=float(error),
                is_anomaly=is_anomaly
            )
            predictions.append(pred)

        return predictions

    def score(self, values: np.ndarray) -> np.ndarray:
        """
        Calculate anomaly scores for a sequence of values.

        Args:
            values: 1D array of time series values

        Returns:
            Array of anomaly scores (reconstruction errors)
        """
        if not TORCH_AVAILABLE or self.model is None:
            return np.zeros(len(values))

        values_norm = self._normalize_data(values)
        device = torch.device(self.config.device)
        self.model.eval()

        scores = []
        seq_len = self.config.sequence_length

        for i in range(seq_len - 1, len(values)):
            sequence = values_norm[i - seq_len + 1:i + 1]
            sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(device)

            with torch.no_grad():
                reconstructed = self.model(sequence_tensor)
                reconstruction = reconstructed.squeeze().cpu().numpy()

            target = values_norm[i]
            recon_target = reconstruction[-1]
            error = (target - recon_target) ** 2
            scores.append(error)

        return np.array(scores)

    def save(self, path: str):
        """
        Save model and state to disk.

        Args:
            path: Directory path to save artifacts
        """
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save config
        config_path = save_path / "lstm_config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'input_size': self.config.input_size,
                'hidden_size': self.config.hidden_size,
                'num_layers': self.config.num_layers,
                'dropout': self.config.dropout,
                'sequence_length': self.config.sequence_length,
                'learning_rate': self.config.learning_rate,
                'batch_size': self.config.batch_size,
                'epochs': self.config.epochs,
                'patience': self.config.patience,
                'threshold_percentile': self.config.threshold_percentile,
                'random_seed': self.config.random_seed,
                'device': self.config.device
            }, f, indent=2)

        # Save state
        state_path = save_path / "lstm_state.json"
        with open(state_path, 'w') as f:
            json.dump({
                'training_loss_history': self.state.training_loss_history,
                'val_loss_history': self.state.val_loss_history,
                'best_val_loss': self.state.best_val_loss,
                'epochs_trained': self.state.epochs_trained,
                'early_stopping_triggered': self.state.early_stopping_triggered,
                'threshold_value': self.state.threshold_value,
                'model_trained': self.state.model_trained,
                'trained_at': self.state.trained_at,
                'scaler_mean': self.scaler_mean,
                'scaler_std': self.scaler_std
            }, f, indent=2)

        # Save model weights
        if self.model is not None and TORCH_AVAILABLE:
            model_path = save_path / "lstm_model.pt"
            torch.save(self.model.state_dict(), model_path)

        logger.info(f"Saved LSTM-AE artifacts to {save_path}")

    def load(self, path: str):
        """
        Load model and state from disk.

        Args:
            path: Directory path containing saved artifacts
        """
        if not TORCH_AVAILABLE:
            logger.error("Cannot load: PyTorch not available")
            return

        load_path = Path(path)

        # Load config
        config_path = load_path / "lstm_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            self.config = LSTMConfig(**config_data)

        # Load state
        state_path = load_path / "lstm_state.json"
        if state_path.exists():
            with open(state_path, 'r') as f:
                state_data = json.load(f)
            self.state.training_loss_history = state_data.get('training_loss_history', [])
            self.state.val_loss_history = state_data.get('val_loss_history', [])
            self.state.best_val_loss = state_data.get('best_val_loss', float('inf'))
            self.state.epochs_trained = state_data.get('epochs_trained', 0)
            self.state.early_stopping_triggered = state_data.get('early_stopping_triggered', False)
            self.state.threshold_value = state_data.get('threshold_value', 0.0)
            self.state.model_trained = state_data.get('model_trained', False)
            self.state.trained_at = state_data.get('trained_at')
            self.scaler_mean = state_data.get('scaler_mean', 0.0)
            self.scaler_std = state_data.get('scaler_std', 1.0)

        # Load model weights
        model_path = load_path / "lstm_model.pt"
        if model_path.exists():
            self._init_model()
            self.model.load_state_dict(torch.load(model_path, map_location=torch.device(self.config.device)))
            logger.info(f"Loaded LSTM-AE model from {model_path}")

    def get_info(self) -> Dict[str, Any]:
        """Return model information for logging/reporting."""
        return {
            'model_type': 'LSTM-Autoencoder',
            'config': {
                'hidden_size': self.config.hidden_size,
                'num_layers': self.config.num_layers,
                'sequence_length': self.config.sequence_length,
                'threshold_percentile': self.config.threshold_percentile
            },
            'state': {
                'trained': self.state.model_trained,
                'epochs_trained': self.state.epochs_trained,
                'threshold_value': self.state.threshold_value,
                'best_val_loss': self.state.best_val_loss
            },
            'parameters': self._count_parameters()
        }


def create_baseline(config: Optional[LSTMConfig] = None) -> LSTMAEBaseline:
    """
    Factory function to create an LSTMAEBaseline instance.

    Args:
        config: Optional LSTMConfig for customization

    Returns:
        LSTMAEBaseline instance
    """
    return LSTMAEBaseline(config=config)


def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(description='LSTM Autoencoder Baseline for Anomaly Detection')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    parser.add_argument('--data', type=str, default=None, help='Path to time series data')
    parser.add_argument('--output', type=str, default='data/processed/results/', help='Output directory')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--hidden-size', type=int, default=64, help='Hidden layer size')
    parser.add_argument('--sequence-length', type=int, default=50, help='Sequence length for LSTM')

    args = parser.parse_args()

    logger.info("Starting LSTM-AE Baseline execution")

    # Create config from arguments
    config = LSTMConfig(
        epochs=args.epochs,
        hidden_size=args.hidden_size,
        sequence_length=args.sequence_length
    )

    # Create baseline
    baseline = create_baseline(config)

    # If no data provided, generate synthetic data for testing
    if args.data is None:
        logger.info("No data provided. Generating synthetic test data...")
        from src.data.synthetic_generator import generate_synthetic_timeseries

        synthetic_data = generate_synthetic_timeseries(
            length=1000,
            noise_level=0.1,
            anomaly_rate=0.05,
            seed=42
        )

        time_series = TimeSeries(
            values=synthetic_data['values'],
            timestamps=[datetime.now() for _ in synthetic_data['values']],
            name='synthetic_test'
        )
    else:
        # Load data from file
        logger.info(f"Loading data from {args.data}")
        # Simple CSV loading - assumes single column of values
        import pandas as pd
        df = pd.read_csv(args.data)
        values = df.iloc[:, 0].values
        time_series = TimeSeries(
            values=values,
            timestamps=[datetime.now() for _ in values],
            name='loaded_data'
        )

    # Train model
    logger.info("Training LSTM-AE model...")
    state = baseline.train(time_series)

    # Generate predictions
    logger.info("Generating predictions...")
    predictions = baseline.predict(time_series)

    # Calculate metrics
    anomaly_count = sum(1 for p in predictions if p.is_anomaly)
    anomaly_rate = anomaly_count / len(predictions) if predictions else 0

    logger.info(f"Training complete. Anomaly rate: {anomaly_rate:.2%}")
    logger.info(f"Total predictions: {len(predictions)}")
    logger.info(f"Anomalies detected: {anomaly_count}")

    # Save results
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save predictions
    pred_path = output_path / "lstm_predictions.json"
    pred_data = [{
        'timestamp': p.timestamp.isoformat(),
        'value': p.value,
        'reconstruction': p.reconstruction,
        'anomaly_score': p.anomaly_score,
        'is_anomaly': p.is_anomaly
    } for p in predictions]
    with open(pred_path, 'w') as f:
        json.dump(pred_data, f, indent=2)

    # Save model
    model_path = output_path / "lstm_model_artifacts"
    baseline.save(model_path)

    # Save summary
    summary_path = output_path / "lstm_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            'model_info': baseline.get_info(),
            'training_state': {
                'epochs_trained': state.epochs_trained,
                'final_val_loss': state.val_loss_history[-1] if state.val_loss_history else None,
                'threshold_value': state.threshold_value
            },
            'results': {
                'total_predictions': len(predictions),
                'anomalies_detected': anomaly_count,
                'anomaly_rate': anomaly_rate
            }
        }, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    print(f"LSTM-AE Baseline complete. Anomaly rate: {anomaly_rate:.2%}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
