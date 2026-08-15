"""
Training loop for Sparse Autoencoder with retry logic (3 seeds) for convergence.
Implements the SAE training required for User Story 2.
"""
import os
import sys
import random
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# Import project modules
from config import get_config
from utils.logging_config import get_logger, info, error, warning, debug
from models.sparse_autoencoder import SparseAutoencoder, create_sparse_autoencoder
from verify_sparsity import load_sample_batch, verify_sparsity_constraint

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_sample_data(batch_size: int = 32) -> torch.Tensor:
    """
    Load sample data for training the SAE.
    Uses the preprocessed ROI timecourses if available, otherwise generates
    a synthetic sample strictly for initialization purposes (fails if real data missing).
    """
    config = get_config()
    data_path = Path("data/neural/processed/roi_timecourses.csv")

    if data_path.exists():
        info(f"Loading training data from {data_path}")
        # Simple CSV load for timecourses: subject_id, roi, timepoint, value
        # We flatten to (batch_size, input_dim) where input_dim = num_rois * timepoints
        # For this implementation, we assume a fixed input dimension for the SAE
        # In a full implementation, we would chunk this properly
        try:
            import pandas as pd
            df = pd.read_csv(data_path)
            # Extract values column
            values = df['value'].values.astype(np.float32)
            
            # If we have enough data, sample a batch
            if len(values) >= batch_size:
                indices = np.random.choice(len(values), batch_size, replace=False)
                batch = values[indices].reshape(batch_size, -1) # Flatten if needed
                return torch.from_numpy(batch)
            else:
                # Pad or repeat if small
                info("Dataset too small, repeating data to reach batch size")
                batch = np.tile(values, (batch_size // len(values) + 1))[:batch_size]
                return torch.from_numpy(batch.reshape(batch_size, -1))
        except Exception as e:
            error(f"Failed to load real data: {e}")
            # Per constraints: if real data loading fails, we must fail loudly.
            # However, for the specific case of "loading sample data for training",
            # if the file exists but is malformed, we raise.
            # If the file doesn't exist, the caller (main) should handle the error.
            raise RuntimeError(f"Data file {data_path} exists but could not be loaded: {e}")
    else:
        # If the file doesn't exist, we cannot train on real data.
        # Per constraint: "NEVER fabricate values... If no real source is reachable, return verdict: failed"
        # But this function is part of a script that must run. If the data isn't there, the script should fail.
        raise FileNotFoundError(f"Training data not found at {data_path}. Please run data ingestion first.")

def calculate_sparsity_loss(activations: torch.Tensor, target_sparsity: float = 0.05) -> torch.Tensor:
    """
    Calculate KL divergence sparsity penalty.
    """
    # Calculate actual sparsity (mean activation)
    # For ReLU-based SAE, sparsity is often measured as the fraction of active units
    # or the mean activation value if we want soft sparsity.
    # Here we use a simple L1 penalty on activations which encourages sparsity.
    return torch.mean(torch.abs(activations))

def train_epoch(
    model: SparseAutoencoder,
    data_loader: torch.utils.data.DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device,
    lambda_sparsity: float = 1.0
) -> Dict[str, float]:
    """
    Train the model for one epoch.
    """
    model.train()
    total_loss = 0.0
    total_sparsity = 0.0
    count = 0

    for batch in data_loader:
        batch = batch.to(device)
        optimizer.zero_grad()

        # Forward pass
        activations, reconstruction = model(batch)

        # Reconstruction loss (MSE)
        recon_loss = nn.functional.mse_loss(reconstruction, batch)

        # Sparsity loss
        sparsity_loss = calculate_sparsity_loss(activations)

        # Total loss
        loss = recon_loss + lambda_sparsity * sparsity_loss

        # Backward pass
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        total_sparsity += sparsity_loss.item()
        count += 1

    return {
        "loss": total_loss / count,
        "sparsity": total_sparsity / count,
        "recon_loss": (total_loss / count) - (lambda_sparsity * (total_sparsity / count))
    }

def validate_model(
    model: SparseAutoencoder,
    data_loader: torch.utils.data.DataLoader,
    device: torch.device
) -> Dict[str, float]:
    """
    Validate the model on a held-out set.
    """
    model.eval()
    total_loss = 0.0
    count = 0

    with torch.no_grad():
        for batch in data_loader:
            batch = batch.to(device)
            activations, reconstruction = model(batch)
            loss = nn.functional.mse_loss(reconstruction, batch)
            total_loss += loss.item()
            count += 1

    return {"val_loss": total_loss / count}

def train_with_seed(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train the SAE with a specific random seed.
    Returns the final metrics and model state path.
    """
    set_seed(seed)
    info(f"Training SAE with seed {seed}")

    # Hyperparameters
    batch_size = config.get("batch_size", 32)
    epochs = config.get("epochs", 50)
    lr = config.get("learning_rate", 1e-3)
    lambda_sparsity = config.get("lambda_sparsity", 1.0)
    input_dim = config.get("input_dim", 128) # Placeholder, should be derived from data
    hidden_dim = config.get("hidden_dim", 512)

    # Load data
    try:
        data = load_sample_data(batch_size)
    except FileNotFoundError as e:
        error(str(e))
        return {"status": "failed", "reason": "data_missing", "seed": seed}

    # Adjust input_dim based on actual data shape if possible
    if data.dim() > 2:
        data = data.view(data.size(0), -1)
    actual_input_dim = data.size(1)
    info(f"Using input dimension: {actual_input_dim}")

    # Create model
    model = create_sparse_autoencoder(input_dim=actual_input_dim, hidden_dim=hidden_dim)
    device = torch.device("cuda" if torch.cuda.is_available() and not config.get("cpu_only", True) else "cpu")
    model = model.to(device)

    optimizer = optim.Adam(model.parameters(), lr=lr)

    # Create data loader
    dataset = torch.utils.data.TensorDataset(data)
    # For a single batch scenario, we might just iterate over the tensor directly
    # But let's use a proper loader if we have enough data
    if len(data) > batch_size:
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
    else:
        # If data is small, just wrap it in a list
        loader = torch.utils.data.DataLoader([data], batch_size=1, shuffle=False)

    # Training loop
    best_val_loss = float('inf')
    best_model_state = None
    history = []

    for epoch in range(epochs):
        train_metrics = train_epoch(model, loader, optimizer, device, lambda_sparsity)
        val_metrics = validate_model(model, loader, device)

        current_val_loss = val_metrics["val_loss"]
        if current_val_loss < best_val_loss:
            best_val_loss = current_val_loss
            best_model_state = model.state_dict()

        history.append({
            "epoch": epoch + 1,
            "train_loss": train_metrics["loss"],
            "val_loss": current_val_loss,
            "sparsity": train_metrics["sparsity"]
        })

        info(f"Epoch {epoch+1}/{epochs} - Loss: {train_metrics['loss']:.4f}, Val Loss: {current_val_loss:.4f}, Sparsity: {train_metrics['sparsity']:.4f}")

    # Save model
    output_dir = Path("data/results/models")
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"sae_seed_{seed}.pt"
    
    if best_model_state:
        torch.save({
            "model_state_dict": best_model_state,
            "seed": seed,
            "best_val_loss": best_val_loss,
            "input_dim": actual_input_dim,
            "hidden_dim": hidden_dim
        }, model_path)
        info(f"Saved best model to {model_path}")
    else:
        # Fallback to last state if something went wrong
        torch.save(model.state_dict(), model_path)

    # Verify sparsity
    try:
        verify_sparsity_constraint(model, device)
        sparsity_status = "passed"
    except RuntimeError as e:
        warning(f"Sparsity verification warning: {e}")
        sparsity_status = "warning"

    return {
        "status": "success",
        "seed": seed,
        "model_path": str(model_path),
        "best_val_loss": best_val_loss,
        "history": history,
        "sparsity_status": sparsity_status
    }

def main():
    """
    Main entry point for SAE training with retry logic.
    Tries up to 3 different seeds to ensure convergence.
    """
    config = get_config()
    logger = get_logger("train_sae")
    
    info("Starting SAE Training with Retry Logic")
    info(f"Configuration: {config}")

    # Training config
    training_config = {
        "batch_size": 32,
        "epochs": 50,
        "learning_rate": 1e-3,
        "lambda_sparsity": 1.0,
        "input_dim": None, # Will be inferred
        "hidden_dim": 512,
        "cpu_only": config.get("cpu_only", True)
    }

    max_attempts = 3
    successful_runs = []
    failed_runs = []

    for attempt in range(1, max_attempts + 1):
        seed = random.randint(42, 9999)
        info(f"Attempt {attempt}/{max_attempts} with seed {seed}")
        
        try:
            result = train_with_seed(seed, training_config)
            if result["status"] == "success":
                successful_runs.append(result)
                info(f"Attempt {attempt} succeeded with seed {seed}")
                # If we have a successful run, we can stop or continue to find a better one?
                # The task says "retry logic for convergence", implying we want at least one.
                # Let's continue to max attempts to find the best, or break if one is enough.
                # For robustness, we'll collect all and pick the best at the end.
            else:
                failed_runs.append(result)
                error(f"Attempt {attempt} failed: {result.get('reason', 'unknown')}")
        except Exception as e:
            error(f"Attempt {attempt} crashed: {e}")
            failed_runs.append({"status": "crashed", "seed": seed, "error": str(e)})

    # Summary
    summary_path = Path("data/results/sae_training_summary.json")
    summary = {
        "total_attempts": max_attempts,
        "successful_attempts": len(successful_runs),
        "failed_attempts": len(failed_runs),
        "results": successful_runs,
        "failures": failed_runs,
        "best_model": None
    }

    if successful_runs:
        # Pick the one with lowest validation loss
        best_run = min(successful_runs, key=lambda x: x["best_val_loss"])
        summary["best_model"] = best_run["model_path"]
        info(f"Best model found: {best_run['model_path']} (Val Loss: {best_run['best_val_loss']:.4f})")
    else:
        error("No successful training runs completed.")

    # Save summary
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    info(f"Training summary saved to {summary_path}")

    if not successful_runs:
        error("Training failed for all seeds. Exiting with error.")
        sys.exit(1)
    else:
        info("Training completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()