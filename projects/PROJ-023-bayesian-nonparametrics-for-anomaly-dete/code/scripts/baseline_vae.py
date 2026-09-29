"""
Baseline VAE Anomaly Detection Script.

Implements a lightweight Variational Autoencoder (VAE) for time series anomaly detection
using PyTorch Lightning (as scikit-learn does not support deep generative models).
Uses reconstruction error as the anomaly score.

Dependencies:
    - torch
    - pytorch-lightning
    - pandas
    - numpy
    - scikit-learn (for metrics)
"""

import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import pytorch_lightning as pl
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.data_loader import load_processed_data
from lib.utils import set_seed, normalize_data, denormalize_data
from lib.memory_profiler import check_memory_usage, profile_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEED = 42
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 1e-3
DEFAULT_HIDDEN_DIM = 64
DEFAULT_LATENT_DIM = 16
DEFAULT_WINDOW_SIZE = 50
DEFAULT_RECONSTRUCTION_THRESHOLD = 0.5
MAX_MEMORY_GB = 7.0


class VAE(nn.Module):
    """
    Variational Autoencoder for 1D time series.

    Architecture:
        Encoder: Input -> Linear -> ReLU -> Linear -> (mu, log_var)
        Decoder: (mu, log_var) -> Linear -> ReLU -> Linear -> Output
    """

    def __init__(self, input_dim: int, hidden_dim: int, latent_dim: int):
        super(VAE, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_log_var = nn.Linear(hidden_dim, latent_dim)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.encoder(x)
        mu = self.fc_mu(h)
        log_var = self.fc_log_var(h)
        return mu, log_var

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        x_recon = self.decode(z)
        return x_recon, mu, log_var, z


class VAEPlModule(pl.LightningModule):
    """
    PyTorch Lightning module for VAE training.
    """

    def __init__(self, input_dim: int, hidden_dim: int, latent_dim: int, lr: float = 1e-3):
        super().__init__()
        self.save_hyperparameters()
        self.vae = VAE(input_dim, hidden_dim, latent_dim)
        self.lr = lr

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_recon, _, _, _ = self.vae(x)
        return x_recon

    def _loss_function(self, x: torch.Tensor, x_recon: torch.Tensor, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        # Reconstruction loss (MSE)
        recon_loss = nn.functional.mse_loss(x_recon, x, reduction='sum')
        
        # KL Divergence loss
        kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
        
        return recon_loss + kl_loss

    def training_step(self, batch, batch_idx):
        x = batch[0]
        x_recon, mu, log_var, _ = self.vae(x)
        loss = self._loss_function(x, x_recon, mu, log_var)
        self.log('train_loss', loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x = batch[0]
        x_recon, mu, log_var, _ = self.vae(x)
        loss = self._loss_function(x, x_recon, mu, log_var)
        self.log('val_loss', loss, prog_bar=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.lr)


def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    pl.seed_everything(seed)
    logger.info(f"Seed set to {seed}")


def check_memory_usage(max_gb: float = MAX_MEMORY_GB) -> None:
    """Check current memory usage and warn if approaching limit."""
    check_memory_usage(max_gb)


def load_and_validate_data(data_path: str) -> pd.DataFrame:
    """
    Load processed time series data and validate schema.
    
    Args:
        data_path: Path to the processed CSV file.
        
    Returns:
        DataFrame with the time series data.
        
    Raises:
        ValueError: If data is missing or invalid.
    """
    logger.info(f"Loading data from {data_path}")
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Validate expected columns
    required_cols = ['timestamp', 'value']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must contain columns: {required_cols}")
    
    # Handle missing values
    if df['value'].isna().any():
        logger.warning("Missing values detected. Interpolating.")
        df['value'] = df['value'].interpolate(method='linear')
    
    # Remove any remaining NaNs at edges
    df = df.dropna(subset=['value'])
    
    logger.info(f"Loaded {len(df)} data points")
    return df


def create_windows(data: np.ndarray, window_size: int, step_size: int = 1) -> Tuple[np.ndarray, List[int]]:
    """
    Create sliding windows from 1D time series.
    
    Args:
        data: 1D array of time series values.
        window_size: Size of each window.
        step_size: Step between windows.
        
    Returns:
        Tuple of (windows, start_indices).
    """
    windows = []
    start_indices = []
    
    for i in range(0, len(data) - window_size + 1, step_size):
        windows.append(data[i:i + window_size])
        start_indices.append(i)
        
    return np.array(windows), start_indices


def train_vae(
    train_loader: DataLoader,
    val_loader: DataLoader,
    input_dim: int,
    hidden_dim: int,
    latent_dim: int,
    epochs: int,
    batch_size: int,
    lr: float,
    device: str,
    checkpoint_path: Optional[str] = None
) -> VAEPlModule:
    """
    Train the VAE model.
    
    Args:
        train_loader: Training data loader.
        val_loader: Validation data loader.
        input_dim: Input dimension.
        hidden_dim: Hidden layer dimension.
        latent_dim: Latent space dimension.
        epochs: Number of training epochs.
        batch_size: Batch size.
        lr: Learning rate.
        device: Device to train on.
        checkpoint_path: Path to save model checkpoint.
        
    Returns:
        Trained VAEPlModule.
    """
    model = VAEPlModule(input_dim, hidden_dim, latent_dim, lr)
    
    # Callbacks
    checkpoint_callback = pl.callbacks.ModelCheckpoint(
        dirpath=checkpoint_path if checkpoint_path else '.',
        filename="vae_best",
        save_top_k=1,
        monitor="val_loss",
        mode="min"
    )
    
    early_stop_callback = pl.callbacks.EarlyStopping(
        monitor="val_loss",
        min_delta=0.00,
        patience=10,
        verbose=True,
        mode="min"
    )
    
    trainer = pl.Trainer(
        max_epochs=epochs,
        accelerator=device,
        devices=1 if device != "cpu" else 1,
        logger=False,
        enable_progress_bar=True,
        enable_checkpointing=True,
        callbacks=[checkpoint_callback, early_stop_callback],
        gradient_clip_val=1.0
    )
    
    trainer.fit(model, train_loader, val_loader)
    
    # Load best model
    best_model_path = checkpoint_callback.best_model_path
    if best_model_path:
        model = VAEPlModule.load_from_checkpoint(best_model_path)
        logger.info(f"Loaded best model from {best_model_path}")
    
    return model


def run_vae_detection(
    model: VAEPlModule,
    test_loader: DataLoader,
    device: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run anomaly detection on test data using reconstruction error.
    
    Args:
        model: Trained VAE model.
        test_loader: Test data loader.
        device: Device to run inference on.
        
    Returns:
        Tuple of (reconstruction_errors, predictions).
    """
    model.to(device)
    model.eval()
    
    reconstruction_errors = []
    
    with torch.no_grad():
        for batch in test_loader:
            x = batch[0].to(device)
            x_recon = model(x)
            
            # Calculate MSE per sample
            mse = torch.mean((x - x_recon) ** 2, dim=1)
            reconstruction_errors.extend(mse.cpu().numpy())
    
    reconstruction_errors = np.array(reconstruction_errors)
    return reconstruction_errors


def save_predictions(
    predictions_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Save predictions to CSV.
    
    Args:
        predictions_df: DataFrame with predictions.
        output_path: Path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    predictions_df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")


def print_summary(
    predictions_df: pd.DataFrame,
    anomaly_count: int,
    total_count: int
) -> None:
    """Print a summary of the detection results."""
    logger.info("=" * 50)
    logger.info("VAE Anomaly Detection Summary")
    logger.info("=" * 50)
    logger.info(f"Total samples: {total_count}")
    logger.info(f"Anomalies detected: {anomaly_count}")
    logger.info(f"Anomaly rate: {anomaly_count / total_count * 100:.2f}%")
    logger.info("=" * 50)


def main():
    """Main entry point for the VAE baseline script."""
    parser = argparse.ArgumentParser(description="VAE Anomaly Detection")
    parser.add_argument("--data", type=str, default="data/processed/series_with_anomalies.csv",
                        help="Path to processed data file")
    parser.add_argument("--output", type=str, default="data/results/vae_predictions.csv",
                        help="Path to output predictions file")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--lr", type=float, default=DEFAULT_LEARNING_RATE, help="Learning rate")
    parser.add_argument("--hidden-dim", type=int, default=DEFAULT_HIDDEN_DIM, help="Hidden dimension")
    parser.add_argument("--latent-dim", type=int, default=DEFAULT_LATENT_DIM, help="Latent dimension")
    parser.add_argument("--window-size", type=int, default=DEFAULT_WINDOW_SIZE, help="Window size")
    parser.add_argument("--threshold", type=float, default=DEFAULT_RECONSTRUCTION_THRESHOLD,
                        help="Anomaly threshold (will be calculated as percentile if not provided)")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use (cpu or cuda)")
    parser.add_argument("--checkpoint-dir", type=str, default="data/results/vae_checkpoints",
                        help="Directory to save model checkpoints")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Check memory
    check_memory_usage()
    
    # Load data
    try:
        df = load_and_validate_data(args.data)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Prepare data
    values = df['value'].values
    timestamps = df['timestamp'].values
    
    # Normalize
    scaler = StandardScaler()
    values_scaled = scaler.fit_transform(values.reshape(-1, 1)).flatten()
    
    # Create windows
    windows, start_indices = create_windows(values_scaled, args.window_size)
    
    # Split into train (80%) and test (20%)
    split_idx = int(len(windows) * 0.8)
    train_windows = windows[:split_idx]
    test_windows = windows[split_idx:]
    test_start_indices = start_indices[split_idx:]
    
    logger.info(f"Train windows: {len(train_windows)}, Test windows: {len(test_windows)}")
    
    # Create data loaders
    train_dataset = TensorDataset(torch.FloatTensor(train_windows))
    test_dataset = TensorDataset(torch.FloatTensor(test_windows))
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Train model
    logger.info("Training VAE model...")
    model = train_vae(
        train_loader, test_loader,
        input_dim=args.window_size,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
        checkpoint_path=args.checkpoint_dir
    )
    
    # Run detection
    logger.info("Running anomaly detection...")
    reconstruction_errors = run_vae_detection(model, test_loader, args.device)
    
    # Determine threshold
    if args.threshold <= 0:
        # Calculate threshold as 95th percentile of training errors (re-run on train)
        model.eval()
        train_errors = []
        with torch.no_grad():
            for batch in train_loader:
                x = batch[0]
                x_recon = model(x)
                mse = torch.mean((x - x_recon) ** 2, dim=1)
                train_errors.extend(mse.cpu().numpy())
        threshold = np.percentile(train_errors, 95)
    else:
        threshold = args.threshold
    
    logger.info(f"Using threshold: {threshold:.4f}")
    
    # Create predictions
    predictions = (reconstruction_errors > threshold).astype(int)
    
    # Map back to original timestamps
    # Only for test windows
    pred_df = pd.DataFrame({
        'timestamp': [timestamps[i] for i in test_start_indices],
        'value': [values[i] for i in test_start_indices],
        'reconstruction_error': reconstruction_errors,
        'anomaly_score': reconstruction_errors / np.max(reconstruction_errors),  # Normalize score
        'is_anomaly': predictions
    })
    
    # Save predictions
    save_predictions(pred_df, args.output)
    
    # Print summary
    print_summary(pred_df, predictions.sum(), len(predictions))
    
    logger.info("VAE baseline completed successfully.")


if __name__ == "__main__":
    main()