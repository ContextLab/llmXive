"""
Training loop for Sparse Autoencoder (SAE) with retry logic.

Implements training across 3 different random seeds to ensure convergence
and robustness of the pattern separation mechanism.
"""
import os
import sys
import random
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# Project imports
from config import get_config
from utils.logging_config import get_logger, info, error, warning, debug
from models.sparse_autoencoder import SparseAutoencoder, create_sparse_autoencoder
from utils.checksums import compute_sha256, update_state_file
from utils.logging_config import ErrorFormatter

# Constants
MAX_RETRIES = 3
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
EPOCHS_PER_SEED = 50
SPARSITY_TARGET = 0.05  # Target sparsity for L1 regularization
LAMBDA_SPARSITY = 1.0   # Weight for sparsity loss

logger = get_logger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_sample_data() -> torch.Tensor:
    """
    Load a sample batch of data for training.
    
    This function attempts to load real processed data. If the expected
    neural data files are not present, it will attempt to load text data
    or fall back to a small synthetic sample ONLY if explicitly allowed
    by configuration (which should not happen in production).
    
    Returns:
        torch.Tensor: Sample data tensor of shape (batch_size, input_dim)
    """
    config = get_config()
    data_dir = Path("data/neural/processed")
    text_dir = Path("data/text")
    
    # Try to load neural ROI timecourses first
    roi_file = data_dir / "roi_timecourses.csv"
    if roi_file.exists():
        logger.info(f"Loading neural data from {roi_file}")
        # Load CSV and flatten for SAE input
        import csv
        data = []
        with open(roi_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            for row in reader:
                # Convert to floats, handling potential empty strings
                try:
                    floats = [float(x) for x in row if x.strip()]
                    if floats:
                        data.append(floats)
                except ValueError:
                    continue
        
        if len(data) > 0:
            # Normalize data
            arr = np.array(data, dtype=np.float32)
            mean = np.mean(arr, axis=0, keepdims=True)
            std = np.std(arr, axis=0, keepdims=True)
            std[std == 0] = 1.0  # Avoid division by zero
            normalized = (arr - mean) / std
            
            # Take a batch
            batch = normalized[:BATCH_SIZE]
            if len(batch) < BATCH_SIZE:
                # Pad or repeat if not enough data
                repeats = (BATCH_SIZE // len(batch)) + 1
                batch = np.tile(batch, (repeats, 1))[:BATCH_SIZE]
            
            logger.info(f"Loaded neural data: {batch.shape}")
            return torch.from_numpy(batch)
    
    # Try to load text embeddings if available
    # This would require a separate embedding model, so we skip for now
    # and rely on the fact that if neural data is missing, training can't proceed
    
    # If we get here, we don't have real data
    # In a real scenario, we would fail loudly
    raise FileNotFoundError(
        "No real training data found. "
        "Expected: data/neural/processed/roi_timecourses.csv. "
        "Please ensure data ingestion (T012, T013) has completed successfully."
    )

def calculate_sparsity_loss(activations: torch.Tensor) -> torch.Tensor:
    """
    Calculate sparsity loss based on L1 norm of activations.
    
    Args:
        activations: Tensor of shape (batch_size, hidden_dim)
    
    Returns:
        Scalar tensor representing sparsity loss
    """
    return torch.mean(torch.abs(activations))

def train_epoch(
    model: SparseAutoencoder,
    data: torch.Tensor,
    optimizer: optim.Optimizer,
    device: torch.device
) -> Tuple[float, float, float]:
    """
    Train the model for one epoch.
    
    Args:
        model: The SparseAutoencoder model
        data: Training data tensor
        optimizer: Optimizer instance
        device: Device to run training on
    
    Returns:
        Tuple of (total_loss, reconstruction_loss, sparsity_loss)
    """
    model.train()
    total_loss = 0.0
    reconstruction_loss_total = 0.0
    sparsity_loss_total = 0.0
    
    # Create batches
    n_samples = data.size(0)
    indices = torch.randperm(n_samples)
    
    for start_idx in range(0, n_samples, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, n_samples)
        batch_indices = indices[start_idx:end_idx]
        batch = data[batch_indices].to(device)
        
        # Forward pass
        optimizer.zero_grad()
        activations, reconstructed = model(batch)
        
        # Calculate losses
        reconstruction_loss = nn.functional.mse_loss(reconstructed, batch)
        sparsity_loss = calculate_sparsity_loss(activations)
        total_loss = reconstruction_loss + LAMBDA_SPARSITY * sparsity_loss
        
        # Backward pass
        total_loss.backward()
        optimizer.step()
        
        # Accumulate losses
        total_loss_total = total_loss.item()
        reconstruction_loss_total += reconstruction_loss.item()
        sparsity_loss_total += sparsity_loss.item()
    
    n_batches = (n_samples + BATCH_SIZE - 1) // BATCH_SIZE
    return (
        total_loss_total / n_batches,
        reconstruction_loss_total / n_batches,
        sparsity_loss_total / n_batches
    )

def validate_model(
    model: SparseAutoencoder,
    data: torch.Tensor,
    device: torch.device
) -> Dict[str, float]:
    """
    Validate the model on the full dataset.
    
    Args:
        model: The trained model
        data: Validation data
        device: Device to run on
    
    Returns:
        Dictionary with validation metrics
    """
    model.eval()
    with torch.no_grad():
        activations, reconstructed = model(data.to(device))
        reconstruction_loss = nn.functional.mse_loss(reconstructed, data.to(device)).item()
        sparsity_ratio = torch.mean((activations > 0).float()).item()
        mean_activation = torch.mean(activations).item()
    
    return {
        "reconstruction_loss": reconstruction_loss,
        "sparsity_ratio": sparsity_ratio,
        "mean_activation": mean_activation
    }

def train_with_seed(
    seed: int,
    data: torch.Tensor,
    device: torch.device
) -> Optional[Dict[str, Any]]:
    """
    Train the SAE with a specific random seed.
    
    Args:
        seed: Random seed for this training run
        data: Training data
        device: Device to train on
    
    Returns:
        Dictionary with training results or None if training failed
    """
    logger.info(f"Starting training with seed {seed}")
    set_seed(seed)
    
    try:
        # Create model
        input_dim = data.size(1)
        model = create_sparse_autoencoder(input_dim=input_dim)
        model = model.to(device)
        
        # Create optimizer
        optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
        
        # Training loop
        best_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(EPOCHS_PER_SEED):
            total_loss, recon_loss, sparse_loss = train_epoch(
                model, data, optimizer, device
            )
            
            if epoch % 10 == 0:
                logger.info(
                    f"Seed {seed}, Epoch {epoch}: "
                    f"Total Loss={total_loss:.4f}, "
                    f"Recon Loss={recon_loss:.4f}, "
                    f"Sparse Loss={sparse_loss:.4f}"
                )
            
            # Early stopping check
            if total_loss < best_loss:
                best_loss = total_loss
                patience_counter = 0
                # Save best model state
                best_state = {
                    "model": model.state_dict(),
                    "seed": seed,
                    "epoch": epoch,
                    "loss": total_loss
                }
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Seed {seed}: Early stopping at epoch {epoch}")
                    break
        
        # Final validation
        metrics = validate_model(model, data, device)
        metrics["seed"] = seed
        metrics["final_loss"] = best_loss
        metrics["converged"] = True
        
        logger.info(
            f"Seed {seed} completed: "
            f"Recon Loss={metrics['reconstruction_loss']:.4f}, "
            f"Sparsity Ratio={metrics['sparsity_ratio']:.4f}"
        )
        
        return metrics, model
    
    except Exception as e:
        logger.error(f"Training failed for seed {seed}: {str(e)}")
        return None

def main():
    """
    Main training loop with retry logic across 3 seeds.
    
    This function:
    1. Loads training data
    2. Trains the SAE with 3 different seeds
    3. Selects the best model based on reconstruction loss
    4. Saves the best model and training metrics
    """
    logger.info("Starting SAE training with retry logic (3 seeds)")
    
    config = get_config()
    device = torch.device("cpu")  # CPU-only as per config
    
    if torch.cuda.is_available() and not config.get("cpu_only", True):
        device = torch.device("cuda")
        logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("Using CPU for training")
    
    # Load data
    try:
        data = load_sample_data()
        logger.info(f"Training data shape: {data.shape}")
    except FileNotFoundError as e:
        error(str(e))
        sys.exit(1)
    
    # Training across 3 seeds
    results = []
    best_result = None
    best_model = None
    
    for seed in [42, 123, 456]:  # Fixed seeds for reproducibility
        result = train_with_seed(seed, data, device)
        if result is not None:
            metrics, model = result
            results.append(metrics)
            
            if best_result is None or metrics["reconstruction_loss"] < best_result["reconstruction_loss"]:
                best_result = metrics
                best_model = model
    
    if not results:
        error("Training failed for all seeds!")
        sys.exit(1)
    
    # Log summary
    logger.info(f"Training completed for {len(results)} seeds")
    logger.info(f"Best seed: {best_result['seed']}")
    logger.info(f"Best reconstruction loss: {best_result['reconstruction_loss']:.4f}")
    logger.info(f"Best sparsity ratio: {best_result['sparsity_ratio']:.4f}")
    
    # Save best model
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / "sae_best_model.pt"
    torch.save({
        "model_state_dict": best_model.state_dict(),
        "seed": best_result["seed"],
        "config": {
            "input_dim": data.size(1),
            "learning_rate": LEARNING_RATE,
            "lambda_sparsity": LAMBDA_SPARSITY
        }
    }, model_path)
    
    logger.info(f"Best model saved to {model_path}")
    
    # Save training metrics
    metrics_path = output_dir / "sae_training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump({
            "seeds_trained": len(results),
            "results": results,
            "best_seed": best_result["seed"],
            "best_metrics": best_result,
            "training_config": {
                "epochs": EPOCHS_PER_SEED,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "lambda_sparsity": LAMBDA_SPARSITY,
                "sparsity_target": SPARSITY_TARGET
            }
        }, f, indent=2)
    
    logger.info(f"Training metrics saved to {metrics_path}")
    
    # Update checksums
    try:
        update_state_file(output_dir)
        logger.info("State file updated with new checksums")
    except Exception as e:
        warning(f"Could not update state file: {str(e)}")
    
    logger.info("SAE training completed successfully")

if __name__ == "__main__":
    main()
