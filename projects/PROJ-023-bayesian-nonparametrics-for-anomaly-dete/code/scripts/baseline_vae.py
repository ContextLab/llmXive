"""
Baseline VAE for Anomaly Detection.

Implements a lightweight Variational Autoencoder using PyTorch Lightning
for CPU-efficient training. Anomalies are detected based on reconstruction error.

Dependencies:
    - torch
    - pytorch-lightning
    - pandas
    - numpy

Output:
    - data/results/vae_predictions.csv
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
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pytorch_lightning as pl
from pytorch_lightning.callbacks import EarlyStopping

# Project local imports
# Ensure the code directory is in the path
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.data_loader import load_processed_data
from lib.memory_profiler import check_memory_usage, MemoryProfiler
from lib.utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_WINDOW_SIZE = 50
DEFAULT_HID_DIM = 64
DEFAULT_LATENT_DIM = 16
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_THRESHOLD_FACTOR = 3.0  # Standard deviations for anomaly threshold
MEMORY_LIMIT_GB = 7.0

class VAE(nn.Module):
    """
    Variational Autoencoder for 1D time series.
    Architecture: Encoder -> Latent (mu, log_var) -> Decoder
    """
    def __init__(self, input_dim: int, hidden_dim: int = 64, latent_dim: int = 16):
        super(VAE, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # Latent space parameters
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

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        x_recon = self.decode(z)
        return x_recon, mu, log_var

class VAEPlModule(pl.LightningModule):
    """
    PyTorch Lightning module wrapper for the VAE.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 64, latent_dim: int = 16, lr: float = 0.001):
        super().__init__()
        self.save_hyperparameters()
        self.vae = VAE(input_dim, hidden_dim, latent_dim)
        self.lr = lr

    def forward(self, x):
        return self.vae(x)

    def training_step(self, batch, batch_idx):
        x, = batch
        x_recon, mu, log_var = self.vae(x)

        # Reconstruction loss (MSE)
        recon_loss = nn.functional.mse_loss(x_recon, x, reduction='sum')

        # KL Divergence loss
        kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())

        loss = recon_loss + kl_loss

        self.log('train_loss', loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, = batch
        x_recon, mu, log_var = self.vae(x)
        recon_loss = nn.functional.mse_loss(x_recon, x, reduction='sum')
        self.log('val_loss', recon_loss, prog_bar=True)
        return recon_loss

    def configure_optimizers(self):
        return optim.Adam(self.parameters(), lr=self.lr)

def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def check_memory_usage():
    """Check current memory usage and exit if limit exceeded."""
    if not check_memory_usage(MEMORY_LIMIT_GB):
        logger.error(f"Memory limit ({MEMORY_LIMIT_GB}GB) exceeded. Stopping execution.")
        sys.exit(1)

def load_and_validate_data(data_path: str) -> pd.DataFrame:
    """
    Load processed time series data from the standard location.
    Validates that the data exists and has the expected columns.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Run data download and preprocessing scripts first.")

    df = pd.read_csv(data_path)

    # Expected columns based on T004/T005 schema
    required_cols = ['timestamp', 'value', 'is_anomaly']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {data_path}")

    logger.info(f"Loaded data with {len(df)} rows from {data_path}")
    return df

def create_windows(series: np.ndarray, window_size: int) -> np.ndarray:
    """
    Create sliding windows from a 1D time series.
    Returns a 2D array of shape (num_windows, window_size).
    """
    windows = []
    for i in range(len(series) - window_size + 1):
        windows.append(series[i:i+window_size])
    return np.array(windows)

def train_vae(
    windows: np.ndarray,
    hidden_dim: int = DEFAULT_HID_DIM,
    latent_dim: int = DEFAULT_LATENT_DIM,
    epochs: int = DEFAULT_EPOCHS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    lr: float = DEFAULT_LEARNING_RATE,
    seed: int = 42
) -> VAEPlModule:
    """
    Train the VAE model on the windowed data.
    """
    set_seed(seed)
    check_memory_usage()

    logger.info(f"Training VAE: hidden={hidden_dim}, latent={latent_dim}, epochs={epochs}")

    # Convert to tensor
    tensor_windows = torch.FloatTensor(windows)
    dataset = TensorDataset(tensor_windows)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    model = VAEPlModule(
        input_dim=windows.shape[1],
        hidden_dim=hidden_dim,
        latent_dim=latent_dim,
        lr=lr
    )

    # Callbacks
    early_stop = EarlyStopping(monitor='val_loss', patience=5, mode='min')

    # Trainer (CPU only as per constraints)
    trainer = pl.Trainer(
        max_epochs=epochs,
        callbacks=[early_stop],
        logger=False, # Disable logger for simplicity in this script
        enable_checkpointing=False,
        accelerator='cpu',
        devices=1
    )

    trainer.fit(model, dataloader)
    logger.info("Training completed.")
    return model

def run_vae_detection(
    model: VAEPlModule,
    windows: np.ndarray,
    window_size: int,
    threshold_factor: float = DEFAULT_THRESHOLD_FACTOR
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run anomaly detection using reconstruction error.
    Returns anomaly scores and binary predictions aligned with original series length.
    """
    model.eval()
    check_memory_usage()

    tensor_windows = torch.FloatTensor(windows)
    dataset = TensorDataset(tensor_windows)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=False)

    reconstruction_errors = []

    with torch.no_grad():
        for batch in dataloader:
            x, = batch
            x_recon, _, _ = model.vae(x)
            # Calculate MSE per window
            mse = torch.mean((x - x_recon) ** 2, dim=1)
            reconstruction_errors.extend(mse.numpy())

    reconstruction_errors = np.array(reconstruction_errors)

    # Calculate threshold based on reconstruction error distribution
    # Using mean + k * std as threshold (similar to Shewhart logic on errors)
    mean_err = np.mean(reconstruction_errors)
    std_err = np.std(reconstruction_errors)
    threshold = mean_err + threshold_factor * std_err

    # Map window-level errors back to time steps
    # Each window corresponds to the last point in the window for alignment
    # Or we can assign the error to all points in the window.
    # Standard approach: assign error to the center or last point.
    # Here we assign to the last point of each window to align with 'current' detection.
    # However, to get a score for every point, we can use a rolling window approach.
    # Since we have (N - W + 1) windows, we will have scores for indices [W-1, N-1].
    # For indices [0, W-2], we can pad with the first error or NaN.
    # To keep it simple and aligned with 'current' detection, we map window i to index i + window_size - 1.

    scores = np.full(len(windows) + window_size - 1, np.nan)
    # Actually, the number of windows is len(series) - window_size + 1.
    # The scores correspond to the end of each window.
    # Let's map index i in windows to timestamp index i + window_size - 1.
    for i, err in enumerate(reconstruction_errors):
        scores[i + window_size - 1] = err

    # Fill NaNs at the beginning with the first valid score
    first_valid_idx = window_size - 1
    if first_valid_idx > 0:
        scores[:first_valid_idx] = scores[first_valid_idx]

    # Binary predictions
    predictions = (scores > threshold).astype(int)

    return scores, predictions

def save_predictions(
    scores: np.ndarray,
    predictions: np.ndarray,
    timestamps: np.ndarray,
    output_path: str
):
    """Save predictions to CSV."""
    df_out = pd.DataFrame({
        'timestamp': timestamps,
        'reconstruction_error': scores,
        'is_anomaly': predictions
    })
    df_out.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

def print_summary(df: pd.DataFrame):
    """Print a summary of the detection results."""
    total = len(df)
    anomalies = df['is_anomaly'].sum()
    logger.info(f"Total points: {total}")
    logger.info(f"Anomalies detected: {anomalies} ({100 * anomalies / total:.2f}%)")

def load_threshold_config(config_path: str) -> float:
    """Load threshold factor from config if available."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('threshold_factor', DEFAULT_THRESHOLD_FACTOR)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using default threshold factor.")
        return DEFAULT_THRESHOLD_FACTOR

def main():
    parser = argparse.ArgumentParser(description='Run VAE Baseline for Anomaly Detection')
    parser.add_argument('--data-path', type=str, default='data/processed/series_with_anomalies.csv',
                        help='Path to processed data CSV')
    parser.add_argument('--output-path', type=str, default='data/results/vae_predictions.csv',
                        help='Path to save predictions')
    parser.add_argument('--window-size', type=int, default=DEFAULT_WINDOW_SIZE,
                        help='Window size for VAE input')
    parser.add_argument('--hidden-dim', type=int, default=DEFAULT_HID_DIM,
                        help='Hidden dimension for VAE')
    parser.add_argument('--latent-dim', type=int, default=DEFAULT_LATENT_DIM,
                        help='Latent dimension for VAE')
    parser.add_argument('--epochs', type=int, default=DEFAULT_EPOCHS,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help='Batch size for training')
    parser.add_argument('--lr', type=float, default=DEFAULT_LEARNING_RATE,
                        help='Learning rate')
    parser.add_argument('--threshold-factor', type=float, default=DEFAULT_THRESHOLD_FACTOR,
                        help='Threshold factor (std deviations)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')

    args = parser.parse_args()

    # Load data
    logger.info("Loading data...")
    df = load_and_validate_data(args.data_path)
    series = df['value'].values
    timestamps = df['timestamp'].values

    # Create windows
    logger.info(f"Creating windows (size={args.window_size})...")
    windows = create_windows(series, args.window_size)
    logger.info(f"Number of windows: {len(windows)}")

    # Train VAE
    logger.info("Training VAE...")
    model = train_vae(
        windows,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed
    )

    # Run detection
    logger.info("Running detection...")
    scores, predictions = run_vae_detection(
        model, windows, args.window_size, args.threshold_factor
    )

    # Save results
    logger.info("Saving results...")
    save_predictions(scores, predictions, timestamps, args.output_path)

    # Summary
    logger.info("Detection Summary:")
    print_summary(df.assign(is_anomaly=predictions))

    logger.info("VAE Baseline completed successfully.")

if __name__ == '__main__':
    main()