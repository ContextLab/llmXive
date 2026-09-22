"""
Baseline VAE (Variational Autoencoder) for Anomaly Detection.

Implements a lightweight VAE using PyTorch (CPU-only) to detect anomalies
based on reconstruction error. This script adheres to the project's
memory constraints and output schema requirements.

Output: data/results/vae_predictions.csv
"""

import os
import sys
import logging
import argparse
import json
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MAX_EPOCHS = 50
BATCH_SIZE = 32
LATENT_DIM = 16
HIDDEN_DIM = 64
LEARNING_RATE = 1e-3
SEED = 42

# Set random seeds for reproducibility
def set_seed(seed: int) -> None:
    """Set random seeds for numpy, torch, and Python."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class VAE(nn.Module):
    """Lightweight Variational Autoencoder for time series anomaly detection."""

    def __init__(self, input_dim: int, hidden_dim: int = HIDDEN_DIM, latent_dim: int = LATENT_DIM):
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
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode input to latent space parameters."""
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Reparameterization trick."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode from latent space."""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass returning reconstruction, mu, and logvar."""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        return recon, mu, logvar

    def get_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Calculate MSE reconstruction error for input."""
        self.eval()
        with torch.no_grad():
            recon, _, _ = self.forward(x)
            mse = torch.mean((x - recon) ** 2, dim=1)
        return mse

def load_and_validate_data(input_path: str) -> pd.DataFrame:
    """Load and validate the input time series data."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(path)

    # Validate columns
    required_cols = ['timestamp', 'value']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input data must contain columns: {required_cols}")

    # Handle missing values
    if df['value'].isnull().any():
        logger.warning("Missing values detected. Interpolating...")
        df['value'] = df['value'].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')

    # Validate data types
    if not np.issubdtype(df['value'].dtype, np.number):
        raise TypeError("Column 'value' must be numeric")

    logger.info(f"Loaded {len(df)} rows. Range: [{df['value'].min():.2f}, {df['value'].max():.2f}]")
    return df

def create_windows(df: pd.DataFrame, window_size: int = 50) -> Tuple[np.ndarray, List[int]]:
    """Create sliding windows for the time series."""
    values = df['value'].values
    windows = []
    indices = []

    for i in range(len(values) - window_size + 1):
        windows.append(values[i:i + window_size])
        indices.append(i + window_size - 1) # Center of the window

    return np.array(windows), indices

def train_vae(model: VAE, train_loader: DataLoader, epochs: int = MAX_EPOCHS, lr: float = LEARNING_RATE) -> VAE:
    """Train the VAE model."""
    device = torch.device("cpu")
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_x, in train_loader:
            batch_x = batch_x.to(device)
            optimizer.zero_grad()

            recon, mu, logvar = model(batch_x)

            # VAE Loss = Reconstruction Loss + KL Divergence
            recon_loss = criterion(recon, batch_x)
            kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            loss = recon_loss + kl_loss

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")

    return model

def run_vae_detection(df: pd.DataFrame, window_size: int = 50) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run VAE anomaly detection pipeline."""
    set_seed(SEED)
    logger.info(f"Starting VAE detection with window size={window_size}")

    # Create windows
    windows, indices = create_windows(df, window_size)
    logger.info(f"Created {len(windows)} windows")

    # Convert to tensors
    tensor_windows = torch.FloatTensor(windows)
    dataset = TensorDataset(tensor_windows)
    train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Initialize and train model
    input_dim = windows.shape[1]
    model = VAE(input_dim=input_dim)
    model = train_vae(model, train_loader)

    # Calculate reconstruction errors
    model.eval()
    errors = model.get_reconstruction_error(tensor_windows).numpy()

    # Calculate threshold (mean + 3*std of errors)
    threshold = np.mean(errors) + 3 * np.std(errors)
    logger.info(f"Anomaly threshold calculated: {threshold:.4f}")

    # Map errors back to original time series
    result_df = pd.DataFrame({
        'timestamp': df['timestamp'].values,
        'value': df['value'].values,
        'reconstruction_error': np.nan, # Initialize with NaN
        'is_anomaly': False
    })

    # Assign errors to the center of the window
    for i, idx in enumerate(indices):
        result_df.loc[idx, 'reconstruction_error'] = errors[i]
        result_df.loc[idx, 'is_anomaly'] = errors[i] > threshold

    # Handle edge cases (first and last window_size-1 points)
    # For simplicity, we mark them as non-anomalous or use the first/last error
    # A more robust approach would use padding or smaller windows at edges
    first_nan_count = result_df['reconstruction_error'].isna().sum()
    if first_nan_count > 0:
        logger.warning(f"First {first_nan_count} and last {first_nan_count} points have no error assigned. Filling with first/last valid error.")
        # Forward fill then backward fill to handle edges
        result_df['reconstruction_error'] = result_df['reconstruction_error'].ffill().bfill()
        result_df['is_anomaly'] = result_df['reconstruction_error'] > threshold

    metrics = {
        'total_points': len(df),
        'anomalies_detected': int(result_df['is_anomaly'].sum()),
        'threshold': float(threshold),
        'mean_error': float(np.mean(errors)),
        'std_error': float(np.std(errors)),
        'window_size': window_size,
        'epochs': MAX_EPOCHS
    }

    return result_df, metrics

def save_predictions(df: pd.DataFrame, output_path: str) -> None:
    """Save predictions to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

def print_summary(metrics: Dict[str, Any]) -> None:
    """Print a summary of the detection results."""
    logger.info("=== VAE Detection Summary ===")
    logger.info(f"Total points analyzed: {metrics['total_points']}")
    logger.info(f"Anomalies detected: {metrics['anomalies_detected']}")
    logger.info(f"Anomaly rate: {metrics['anomalies_detected']/metrics['total_points']*100:.2f}%")
    logger.info(f"Threshold: {metrics['threshold']:.4f}")
    logger.info(f"Mean reconstruction error: {metrics['mean_error']:.4f}")
    logger.info(f"Std reconstruction error: {metrics['std_error']:.4f}")

def check_memory_usage() -> None:
    """Check current memory usage against limit."""
    current, peak = tracemalloc.get_traced_memory()
    peak_gb = peak / (1024 ** 3)
    logger.info(f"Current memory: {current/1024/1024:.2f} MB, Peak memory: {peak_gb:.2f} GB")
    if peak_gb > MEMORY_LIMIT_GB:
        logger.error(f"Memory limit exceeded! Peak: {peak_gb:.2f} GB > {MEMORY_LIMIT_GB} GB")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run VAE Anomaly Detection")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/series_with_anomalies.csv",
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/vae_predictions.csv",
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=50,
        help="Sliding window size"
    )
    args = parser.parse_args()

    tracemalloc.start()

    try:
        # Load data
        df = load_and_validate_data(args.input)

        # Run detection
        result_df, metrics = run_vae_detection(df, window_size=args.window_size)

        # Save results
        save_predictions(result_df, args.output)

        # Print summary
        print_summary(metrics)

        # Check memory
        check_memory_usage()

        logger.info("VAE detection completed successfully.")

    except Exception as e:
        logger.error(f"Error during VAE detection: {e}")
        raise
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()