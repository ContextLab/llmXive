"""
Baseline VAE for Anomaly Detection.

Implements a lightweight Variational Autoencoder (VAE) using PyTorch for
CPU-based anomaly detection via reconstruction error.

This script consumes preprocessed time series data (from T004/T006),
trains a VAE, computes reconstruction errors, and outputs anomaly scores
to `data/results/vae_predictions.csv`.

Dependencies:
    - torch
    - numpy
    - pandas
    - scikit-learn
"""

import os
import sys
import logging
import argparse
import json
import time
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/vae_training.log')
    ]
)
logger = logging.getLogger(__name__)

# Suppress specific warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='torch')

# --- Configuration Constants ---
DEFAULT_SEED = 42
DEFAULT_WINDOW_SIZE = 50
DEFAULT_HORIZON = 1
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 64
DEFAULT_LEARNING_RATE = 1e-3
DEFAULT_LATENT_DIM = 16
DEFAULT_HIDDEN_DIM = 64
DEFAULT_RECONSTRUCTION_WEIGHT = 1.0
DEFAULT_KL_WEIGHT = 0.001
DEFAULT_MEMORY_LIMIT_GB = 7.0

# --- Helper Functions ---

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Random seed set to {seed}")

def check_memory_usage(limit_gb: float = DEFAULT_MEMORY_LIMIT_GB) -> None:
    """
    Check current memory usage against the limit.
    Raises SystemExit if exceeded.
    """
    try:
        import tracemalloc
        current, peak = tracemalloc.get_traced_memory()
        peak_gb = peak / (1024 ** 3)
        if peak_gb > limit_gb:
            logger.error(f"Peak memory usage ({peak_gb:.2f} GB) exceeds limit ({limit_gb} GB)")
            raise SystemExit(1)
        logger.info(f"Current memory: {current / (1024 ** 2):.2f} MB, Peak: {peak_gb:.4f} GB")
    except ImportError:
        logger.warning("tracemalloc not available, skipping memory check")

def load_and_validate_data(data_path: str) -> pd.DataFrame:
    """
    Load and validate the preprocessed time series data.
    Expects a CSV with a 'value' column and optional 'timestamp'.
    """
    path = Path(data_path)
    if not path.exists():
        logger.error(f"Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # Validate required columns
    if 'value' not in df.columns:
        logger.error("Data must contain a 'value' column")
        raise ValueError("Data must contain a 'value' column")

    # Handle missing values
    if df['value'].isnull().any():
        logger.warning("Missing values detected. Interpolating...")
        df['value'] = df['value'].interpolate(method='linear').ffill().bfill()

    # Drop any remaining NaNs
    df = df.dropna(subset=['value'])

    if len(df) == 0:
        logger.error("Data is empty after cleaning")
        raise ValueError("Data is empty after cleaning")

    logger.info(f"Loaded {len(df)} data points from {data_path}")
    return df

def create_windows(
    data: np.ndarray,
    window_size: int,
    horizon: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sliding windows for VAE training.
    Input: 1D array of shape (N,)
    Output: X (N-window_size+1, window_size), y (N-window_size+1, horizon)
    """
    X, y = [], []
    for i in range(len(data) - window_size - horizon + 1):
        X.append(data[i : i + window_size])
        y.append(data[i + window_size : i + window_size + horizon])

    return np.array(X), np.array(y)

# --- VAE Model Definition ---

class VAE(nn.Module):
    """
    Variational Autoencoder for 1D time series.
    Architecture: Linear -> ReLU -> Linear (Latent)
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
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim * 2) # mu and log_var
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.encoder(x)
        mu, log_var = h[:, :self.latent_dim], h[:, self.latent_dim:]
        z = self.reparameterize(mu, log_var)
        x_recon = self.decoder(z)
        return x_recon, mu, log_var

    def loss_function(self, x: torch.Tensor, x_recon: torch.Tensor, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        """
        VAE Loss: Reconstruction Loss + KL Divergence
        """
        BCE = nn.functional.mse_loss(x_recon, x, reduction='sum')
        # KL Divergence: -0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
        KLD = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
        return BCE + KLD

# --- Training and Inference ---

def train_vae(
    model: VAE,
    train_loader: DataLoader,
    epochs: int,
    lr: float,
    device: torch.device,
    recon_weight: float = DEFAULT_RECONSTRUCTION_WEIGHT,
    kl_weight: float = DEFAULT_KL_WEIGHT
) -> List[float]:
    """Train the VAE model."""
    optimizer = optim.Adam(model.parameters(), lr=lr)
    model.train()
    losses = []

    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, _ in train_loader:
            batch_x = batch_x.to(device)
            optimizer.zero_grad()

            x_recon, mu, log_var = model(batch_x)
            loss = model.loss_function(batch_x, x_recon, mu, log_var)

            # Apply weights
            loss = recon_weight * loss # KL weight is usually part of the loss function logic, but here we scale total
            # Note: Standard VAE loss is BCE + KLD. If we want to balance, we can scale KLD specifically.
            # Let's stick to the standard loss function defined in the model and just scale the total if needed,
            # or modify the loss function call. For simplicity, we use the model's internal loss.
            # To support KL weight explicitly as per common practices:
            # We will re-implement the loss calculation here to allow separate weighting if needed,
            # or assume the model's loss_function is the standard one.
            # Let's use the standard one and just optimize it.
            # If specific weighting is required, we adjust the loss function call.
            # For this implementation, we assume the model.loss_function returns standard BCE + KLD.
            # To allow KL weighting, we modify the calculation:
            BCE = nn.functional.mse_loss(x_recon, batch_x, reduction='sum')
            KLD = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
            loss = BCE + kl_weight * KLD

            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader.dataset)
        losses.append(avg_loss)
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")

    return losses

def run_vae_detection(
    data_path: str,
    output_path: str,
    window_size: int = DEFAULT_WINDOW_SIZE,
    horizon: int = DEFAULT_HORIZON,
    epochs: int = DEFAULT_EPOCHS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    lr: float = DEFAULT_LEARNING_RATE,
    hidden_dim: int = DEFAULT_HIDDEN_DIM,
    latent_dim: int = DEFAULT_LATENT_DIM,
    seed: int = DEFAULT_SEED,
    device: Optional[str] = None
) -> None:
    """
    Main detection pipeline: Load, Preprocess, Train, Predict, Save.
    """
    set_seed(seed)

    # Device selection
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device)
    logger.info(f"Using device: {device}")

    # Load Data
    df = load_and_validate_data(data_path)
    values = df['value'].values.astype(np.float32)

    # Normalize
    scaler = StandardScaler()
    values_scaled = scaler.fit_transform(values.reshape(-1, 1)).flatten()

    # Create Windows
    X, _ = create_windows(values_scaled, window_size, horizon)
    logger.info(f"Created {len(X)} windows of size {window_size}")

    if len(X) < 10:
        logger.error("Not enough data to create windows. Increase data length or decrease window size.")
        raise ValueError("Insufficient data for windowing")

    # Split Data
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=seed)
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Convert to Tensors
    X_train_tensor = torch.FloatTensor(X_train)
    X_test_tensor = torch.FloatTensor(X_test)

    train_dataset = TensorDataset(X_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Initialize Model
    input_dim = window_size
    model = VAE(input_dim, hidden_dim, latent_dim).to(device)
    logger.info(f"Model architecture: Input={input_dim}, Hidden={hidden_dim}, Latent={latent_dim}")

    # Train
    logger.info("Starting training...")
    start_time = time.time()
    losses = train_vae(model, train_loader, epochs, lr, device)
    training_time = time.time() - start_time
    logger.info(f"Training completed in {training_time:.2f} seconds")

    # Inference on Full Data (Sliding Window)
    # We need to reconstruct every window to get scores for every point
    # We'll use the test set logic but on the full scaled data
    X_full_tensor = torch.FloatTensor(X).to(device)
    model.eval()

    reconstruction_errors = []
    with torch.no_grad():
        for i in range(0, len(X_full_tensor), batch_size):
            batch = X_full_tensor[i : i + batch_size]
            x_recon, _, _ = model(batch)
            # Calculate MSE per sample
            mse = torch.mean((batch - x_recon) ** 2, dim=1)
            reconstruction_errors.extend(mse.cpu().numpy().tolist())

    reconstruction_errors = np.array(reconstruction_errors)

    # Map errors back to original time steps
    # Each error corresponds to a window starting at index i
    # We assign the error to the center of the window or the last point?
    # Standard practice: assign to the last point of the window (t + window_size)
    # Or center. Let's assign to the center for symmetry.
    # Window i covers [i, i + window_size)
    # Center index: i + window_size // 2
    # We will create a scores array of length len(values)
    scores = np.full(len(values), np.nan)
    for i, error in enumerate(reconstruction_errors):
        center_idx = i + window_size // 2
        if center_idx < len(values):
            scores[center_idx] = error

    # Interpolate NaNs at the edges
    scores = pd.Series(scores).interpolate(method='linear').bfill().ffill().values

    # Create Output DataFrame
    # Align with original index
    output_df = df.copy()
    output_df['reconstruction_error'] = scores
    output_df['anomaly_score'] = scores # Normalize to 0-1 or keep raw? Task says "anomaly scores"
    # Let's normalize to 0-1 using max-min for interpretability
    min_err = np.min(scores)
    max_err = np.max(scores)
    if max_err > min_err:
        output_df['anomaly_score'] = (scores - min_err) / (max_err - min_err)
    else:
        output_df['anomaly_score'] = 0.0

    # Determine binary flag (simple threshold: top 5% or > 2 std dev?)
    # Task T022 says "output anomaly scores". T026a handles thresholding.
    # But we should output a binary flag if possible or just the score.
    # Let's output the score and a binary flag based on 95th percentile for now.
    threshold = np.percentile(scores, 95)
    output_df['is_anomaly'] = (scores > threshold).astype(int)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

    # Memory Check
    check_memory_usage()

def save_predictions(df: pd.DataFrame, path: str) -> None:
    """Save predictions to CSV."""
    df.to_csv(path, index=False)

def print_summary(df: pd.DataFrame, path: str) -> None:
    """Print summary statistics of the output."""
    logger.info(f"Output saved to {path}")
    logger.info(f"Total points: {len(df)}")
    logger.info(f"Anomalies detected: {df['is_anomaly'].sum()}")
    logger.info(f"Mean reconstruction error: {df['reconstruction_error'].mean():.4f}")
    logger.info(f"Max reconstruction error: {df['reconstruction_error'].max():.4f}")

def main() -> None:
    parser = argparse.ArgumentParser(description="VAE Baseline for Anomaly Detection")
    parser.add_argument("--input", type=str, required=True, help="Path to input data CSV")
    parser.add_argument("--output", type=str, default="data/results/vae_predictions.csv", help="Path to output CSV")
    parser.add_argument("--window-size", type=int, default=DEFAULT_WINDOW_SIZE, help="Window size for sliding window")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--lr", type=float, default=DEFAULT_LEARNING_RATE, help="Learning rate")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--device", type=str, default=None, help="Device (cpu/cuda)")

    args = parser.parse_args()

    try:
        run_vae_detection(
            data_path=args.input,
            output_path=args.output,
            window_size=args.window_size,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            seed=args.seed,
            device=args.device
        )
    except Exception as e:
        logger.error(f"VAE Detection failed: {e}")
        raise

if __name__ == "__main__":
    main()